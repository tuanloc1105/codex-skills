import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import test from 'node:test';
import { collectBoundedMongoCursor } from '../src/adapters/mongodb.js';
import { collectOracleResultSet } from '../src/adapters/oracle.js';
import {
  collectPostgresqlCursor,
  executePostgresqlMutationStreaming,
} from '../src/adapters/postgresql.js';
import {
  streamSqlServerMutation,
  streamSqlServerQuery,
} from '../src/adapters/sqlserver.js';

test('PostgreSQL cursor fetches one row at a time and stops on the row cap', async () => {
  const queued = [{ id: 1 }, { id: 2 }, { id: 3 }];
  const reads = [];
  let closed = false;
  const cursor = {
    async read(count) {
      reads.push(count);
      return queued.length > 0 ? [queued.shift()] : [];
    },
    async close() { closed = true; },
  };
  const result = await collectPostgresqlCursor(cursor, 2);
  assert.deepEqual(reads, [1, 1, 1]);
  assert.equal(result.rows.length, 2);
  assert.equal(result.truncationReason, 'max-rows');
  assert.equal(closed, true);
});

test('PostgreSQL mutation streams and discards RETURNING rows', async () => {
  class FakeQuery extends EventEmitter {
    constructor(sql) {
      super();
      this.sql = sql;
    }
  }
  const resultEntry = { command: 'UPDATE', rowCount: 2 };
  const client = {
    query(query) {
      queueMicrotask(() => {
        query.emit('row', { payload: Buffer.alloc(1024 * 1024) }, resultEntry);
        query.emit('row', { payload: Buffer.alloc(1024 * 1024) }, resultEntry);
        query.emit('end', resultEntry);
      });
    },
  };
  assert.deepEqual(
    await executePostgresqlMutationStreaming(client, FakeQuery, 'UPDATE t SET x = 1 RETURNING *'),
    {
      statements: [{ command: 'UPDATE', rowCount: 2, returnedRowsDiscarded: 2 }],
      statementCount: 1,
      statementsTruncated: false,
      returnedRowsDiscarded: 2,
    },
  );
});

test('Oracle result sets fetch incrementally and close omitted LOBs', async () => {
  const BLOB = {};
  const closedLobs = [];
  const lob = (length) => ({
    type: BLOB,
    length,
    async close() { closedLobs.push(length); },
  });
  const queued = [[lob(5000), Buffer.alloc(8)], [lob(9000), Buffer.alloc(8)]];
  let resultSetClosed = false;
  const resultSet = {
    async getRow() { return queued.shift(); },
    async close() { resultSetClosed = true; },
  };
  const result = await collectOracleResultSet(resultSet, 1, { DB_TYPE_BLOB: BLOB });
  assert.equal(result.rows[0][0].$oracleLob.length, 5000);
  assert.equal(result.rows[0][0].$oracleLob.contentOmitted, true);
  assert.equal(result.truncationReason, 'max-rows');
  assert.deepEqual(closedLobs, [5000, 9000]);
  assert.equal(resultSetClosed, true);
});

class FakeSqlRequest extends EventEmitter {
  constructor(run) {
    super();
    this.run = run;
    this.cancelled = false;
  }

  query() {
    queueMicrotask(() => this.run(this));
    return new Promise(() => {});
  }

  cancel() {
    this.cancelled = true;
    queueMicrotask(() => this.emit('error', Object.assign(new Error('cancelled'), { code: 'ECANCEL' })));
  }
}

test('SQL Server read cancels streaming at row and byte budgets', async () => {
  let rowRequest;
  const rowPool = {
    request() {
      rowRequest = new FakeSqlRequest((request) => {
        request.emit('recordset', { id: { type: { name: 'Int' } } });
        request.emit('row', { id: 1 });
        request.emit('row', { id: 2 });
      });
      return rowRequest;
    },
  };
  const rowResult = await streamSqlServerQuery(rowPool, 'SELECT id FROM t', 1, 1000);
  assert.equal(rowRequest.cancelled, true);
  assert.equal(rowResult.rowCount, 1);
  assert.equal(rowResult.truncationReason, 'max-rows');

  let byteRequest;
  const bytePool = {
    request() {
      byteRequest = new FakeSqlRequest((request) => {
        request.emit('recordset', { payload: { type: { name: 'VarChar' } } });
        request.emit('row', { payload: 'x'.repeat(1000) });
      });
      return byteRequest;
    },
  };
  const byteResult = await streamSqlServerQuery(bytePool, 'SELECT payload FROM t', 10, 1000, 100);
  assert.equal(byteRequest.cancelled, true);
  assert.equal(byteResult.rowCount, 0);
  assert.equal(byteResult.truncationReason, 'max-output-bytes');
});

test('SQL Server mutation discards OUTPUT rows and caps statement counters', async () => {
  const pool = {
    request() {
      return new FakeSqlRequest((request) => {
        for (let index = 0; index < 3; index += 1) request.emit('row', { id: index });
        for (let index = 0; index < 1100; index += 1) request.emit('rowsaffected', 1);
        request.emit('done');
      });
    },
  };
  const result = await streamSqlServerMutation(pool, 'UPDATE t SET x = 1 OUTPUT inserted.id', 1000);
  assert.equal(result.returnedRowsDiscarded, 3);
  assert.equal(result.rowsAffected.length, 1000);
  assert.equal(result.rowsAffectedTruncated, true);
});

class FakeMongoCursor {
  constructor(values) {
    this.values = values;
    this.closed = false;
  }

  async *[Symbol.asyncIterator]() {
    for (const value of this.values) yield value;
  }

  async close() { this.closed = true; }
}

test('MongoDB cursors enforce row, byte, and total deadline bounds', async () => {
  const rowsCursor = new FakeMongoCursor([{ id: 1 }, { id: 2 }, { id: 3 }]);
  const rows = await collectBoundedMongoCursor(rowsCursor, 2);
  assert.equal(rows.values.length, 2);
  assert.equal(rows.truncationReason, 'max-rows');
  assert.equal(rowsCursor.closed, true);

  const bytesCursor = new FakeMongoCursor([{ payload: 'x'.repeat(1000) }]);
  const bytes = await collectBoundedMongoCursor(bytesCursor, 10, { maxBytes: 100 });
  assert.equal(bytes.values.length, 0);
  assert.equal(bytes.truncationReason, 'max-output-bytes');

  const expiredCursor = new FakeMongoCursor([{ id: 1 }]);
  await assert.rejects(
    collectBoundedMongoCursor(expiredCursor, 10, { deadline: Date.now() - 1 }),
    { code: 'DATABASE_TIMEOUT' },
  );
  assert.equal(expiredCursor.closed, true);
});
