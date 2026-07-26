import assert from 'node:assert/strict';
import test from 'node:test';
import { mongoClientOptions, mongoHelloServerIdentity } from '../src/adapters/mongodb.js';

test('MongoDB client disables automatic write retries', () => {
  const options = mongoClientOptions({
    connection: { database: 'application', authSource: 'admin', tls: false },
  }, { username: 'writer', secret: 'do-not-print' }, 1234);
  assert.equal(options.retryWrites, false);
  assert.equal(options.serverSelectionTimeoutMS, 1234);
  assert.equal(options.auth.password, 'do-not-print');
});

test('MongoDB hello identity uses an accessible stable topology identifier', () => {
  assert.equal(mongoHelloServerIdentity({ setName: 'rs0' }), 'set:rs0');
  assert.equal(mongoHelloServerIdentity({ me: 'mongo-1.internal:27017' }), 'address:mongo-1.internal:27017');
  assert.equal(mongoHelloServerIdentity({ topologyVersion: { processId: { toString: () => 'process-a' } } }), 'process:process-a');
  assert.equal(mongoHelloServerIdentity({
    setName: 'rs0', topologyVersion: { processId: { toString: () => 'process-a' } },
  }), 'set:rs0|process:process-a');
  assert.notEqual(mongoHelloServerIdentity({
    setName: 'rs0', topologyVersion: { processId: { toString: () => 'process-a' } },
  }), mongoHelloServerIdentity({
    setName: 'rs0', topologyVersion: { processId: { toString: () => 'process-b' } },
  }));
  assert.equal(mongoHelloServerIdentity({}), null);
});
