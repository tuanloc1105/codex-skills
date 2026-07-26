import assert from 'node:assert/strict';
import test from 'node:test';
import { postgresqlIdentityFromRow } from '../src/adapters/postgresql.js';
import { verifyPlannedIdentity } from '../src/adapters/common.js';

const target = {
  engine: 'postgresql',
  connection: { host: 'db.internal', port: 5432, database: 'payments', tls: false },
};
const credential = { username: 'writer', secret: 'unused', mode: 'mutation' };
const readCredential = { username: 'reader', secret: 'unused', mode: 'read' };
const row = {
  database: 'payments',
  principal: 'writer',
  server_identity: '10.0.0.12',
  cluster_system_identifier: '7619085564977514241',
  version: 'PostgreSQL 17.5',
};

test('PostgreSQL identity includes the cluster system identifier', () => {
  const identity = postgresqlIdentityFromRow(target, credential, row);
  assert.equal(identity.clusterSystemIdentifier, row.cluster_system_identifier);
});

test('PostgreSQL identity fails closed without a cluster system identifier', () => {
  assert.throws(
    () => postgresqlIdentityFromRow(target, credential, { ...row, cluster_system_identifier: null }),
    { code: 'TARGET_IDENTITY_MISMATCH' },
  );
});

test('PostgreSQL read identity does not require or expose a cluster system identifier', () => {
  const { cluster_system_identifier: _omitted, ...readRow } = row;
  const identity = postgresqlIdentityFromRow(target, readCredential, readRow);
  assert.equal(identity.database, row.database);
  assert.equal(Object.hasOwn(identity, 'clusterSystemIdentifier'), false);
});

test('PostgreSQL mutation identity detects a different cluster at the same endpoint', () => {
  const expected = postgresqlIdentityFromRow(target, credential, row);
  const actual = postgresqlIdentityFromRow(target, credential, {
    ...row,
    cluster_system_identifier: '7619085564977514999',
  });

  assert.equal(actual.database, expected.database);
  assert.equal(actual.principal, expected.principal);
  assert.equal(actual.serverIdentity, expected.serverIdentity);
  assert.throws(
    () => verifyPlannedIdentity(expected, actual),
    { code: 'TARGET_IDENTITY_MISMATCH' },
  );
});

test('PostgreSQL mutation identity rejects a legacy plan without cluster identity', () => {
  const actual = postgresqlIdentityFromRow(target, credential, row);
  const { clusterSystemIdentifier: _omitted, ...legacyExpected } = actual;
  assert.throws(
    () => verifyPlannedIdentity(legacyExpected, actual),
    { code: 'TARGET_IDENTITY_MISMATCH' },
  );
});
