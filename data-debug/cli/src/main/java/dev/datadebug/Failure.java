package dev.datadebug;

/** Messages never include configuration values or raw driver diagnostics. */
final class Failure extends Exception {
    final String code, transport, transaction;
    Failure(String code) { this(code, "not-connected", "not-started"); }
    Failure(String code, String transport, String transaction) {
        super(code); this.code = code; this.transport = transport; this.transaction = transaction;
    }
    String json() {
        return "{\"error\":" + Json.quote(code) + ",\"transport\":" + Json.quote(transport) + ",\"transaction\":" + Json.quote(transaction) + "}";
    }
}
