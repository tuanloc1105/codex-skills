export class AgentDbError extends Error {
  constructor(code, message, details = undefined, exitCode = 1) {
    super(message);
    this.name = 'AgentDbError';
    this.code = code;
    this.details = details;
    this.exitCode = exitCode;
  }
}

export function invariant(condition, code, message, details = undefined) {
  if (!condition) {
    throw new AgentDbError(code, message, details);
  }
}

export function safeError(error) {
  if (error instanceof AgentDbError) {
    return {
      code: error.code,
      message: error.message,
      ...(error.details === undefined ? {} : { details: error.details }),
    };
  }

  return {
    code: 'INTERNAL_ERROR',
    message: error instanceof Error ? error.message : 'Unexpected error',
  };
}
