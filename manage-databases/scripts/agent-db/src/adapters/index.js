import { AgentDbError } from '../core/errors.js';
import { createMongoAdapter } from './mongodb.js';
import { createOracleAdapter } from './oracle.js';
import { createPostgresqlAdapter } from './postgresql.js';
import { createSqlServerAdapter } from './sqlserver.js';

export async function createAdapter(target, credential) {
  switch (target.engine) {
    case 'mongodb': return createMongoAdapter(target, credential);
    case 'oracle': return createOracleAdapter(target, credential);
    case 'postgresql': return createPostgresqlAdapter(target, credential);
    case 'sqlserver': return createSqlServerAdapter(target, credential);
    default: throw new AgentDbError('UNSUPPORTED_ENGINE', `Unsupported database engine: ${target.engine}`);
  }
}
