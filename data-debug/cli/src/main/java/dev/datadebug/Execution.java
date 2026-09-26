package dev.datadebug;

import java.sql.*;
import java.util.Map;
import java.util.concurrent.*;

final class Execution {
    @FunctionalInterface interface Connector { Connection open(Adapter.Request request) throws SQLException; }
    private volatile Connection current;
    private volatile boolean cancelled;
    private volatile String transport = "not-connected", transaction = "not-started";
    static String run(Options o, Map<String, String> fields, String input, Connector connector) throws Failure {
        Adapter.Target target = Adapter.target(o, fields);
        Sql.Checked sql = Sql.check(input, o.engine, o.mode.equals("write"));
        Execution execution = new Execution();
        ExecutorService worker = Executors.newSingleThreadExecutor(r -> { Thread t = new Thread(r, "data-debug-jdbc"); t.setDaemon(true); return t; });
        Future<String> future = worker.submit(() -> execution.perform(o, target, sql, connector));
        try { return future.get(o.timeout, TimeUnit.SECONDS); }
        catch (TimeoutException e) {
            execution.cancelled = true;
            future.cancel(true);
            Connection c = execution.current;
            if (c != null) {
                Thread abort = new Thread(() -> { try { c.abort(Runnable::run); } catch (SQLException ignored) { } }, "data-debug-abort");
                abort.setDaemon(true); abort.start();
            }
            throw new Failure("TIMEOUT", execution.transport, "unknown");
        } catch (InterruptedException e) { execution.cancelled = true; future.cancel(true); Thread.currentThread().interrupt(); throw new Failure("TIMEOUT", execution.transport, "unknown"); }
        catch (ExecutionException e) {
            if (e.getCause() instanceof Failure f) throw f;
            throw new Failure("EXECUTION", execution.transport, execution.transaction);
        } finally { worker.shutdownNow(); }
    }
    static void checkInterrupted() throws Failure { if (Thread.currentThread().isInterrupted()) throw new Failure("TIMEOUT"); }
    private void checkActive() throws Failure { if (cancelled) throw new Failure("TIMEOUT"); checkInterrupted(); }
    private String perform(Options o, Adapter.Target target, Sql.Checked sql, Connector connector) throws Failure {
        boolean write = o.mode.equals("write"), executing = false, commitAttempted = false;
        String tls = o.tls;
        try {
            checkActive();
            try { current = connector.open(Adapter.request(target, o, tls)); }
            catch (SQLException e) {
                String state = e.getSQLState();
                if (!tls.equals("verified") || (state != null && state.startsWith("28")) || !Adapter.certificateFailure(e)) throw e;
                checkActive(); tls = "relaxed";
                current = connector.open(Adapter.request(target, o, tls));
            }
            transport = tls.equals("plaintext") ? "plaintext-requested-server-may-encrypt" : tls + "-encrypted";
            checkActive();
            current.setAutoCommit(false);
            transaction = "started";
            current.setReadOnly(!write);
            if (!write && o.engine.equals("oracle")) {
                try (Statement control = current.createStatement()) { control.setQueryTimeout(o.timeout); control.execute("SET TRANSACTION READ ONLY"); }
            }
            // Server metadata is inspected internally only; never log target names/versions automatically.
            current.getMetaData().getDatabaseMajorVersion();
            String data;
            try (Statement s = current.createStatement()) {
                s.setQueryTimeout(o.timeout); s.setMaxRows(o.rows + 1);
                if (o.engine.equals("mysql")) s.setFetchSize(Integer.MIN_VALUE); else s.setFetchSize(Math.min(o.rows + 1, 100));
                checkActive(); executing = true;
                boolean result = s.execute(sql.text()); // Exactly one user statement; never reconnect after this point.
                if (result) {
                    try (ResultSet rs = s.getResultSet()) { data = Results.read(rs, o.rows); }
                } else data = "\"updateCount\":" + s.getLargeUpdateCount() + ",\"truncated\":false";
            }
            checkActive();
            if (write) {
                commitAttempted = true; transaction = "commit-unknown";
                current.commit(); transaction = sql.ddl() && implicitDdl(o.engine) ? "committed-ddl-may-auto-commit" : "committed";
            } else { current.rollback(); transaction = "read-rolled-back"; }
            return "{\"engine\":" + Json.quote(o.engine) + ",\"mode\":" + Json.quote(o.mode) + ",\"transport\":" + Json.quote(transport) +
                ",\"transaction\":" + Json.quote(transaction) + ",\"ddlRecovery\":" + Json.quote(sql.ddl() ? "may-require-manual-recovery" : "transactional-where-supported") + "," + data + "}";
        } catch (Exception e) {
            boolean rolledBack = false;
            if (current != null && transaction.equals("started")) {
                try { current.rollback(); rolledBack = true; } catch (SQLException ignored) { }
            }
            if (commitAttempted) transaction = "commit-unknown";
            else if (executing && sql.ddl() && implicitDdl(o.engine)) transaction = "ddl-may-have-auto-committed";
            else if (executing && write) transaction = rolledBack ? "rollback-requested-effects-not-guaranteed" : "unknown";
            else if (rolledBack) transaction = "rolled-back";
            String code = e instanceof Failure f ? f.code : e instanceof SQLException s ? Adapter.errorCode(s) : "EXECUTION";
            throw new Failure(code, transport, transaction);
        } finally {
            if (current != null) { try { current.close(); } catch (SQLException ignored) { } }
        }
    }
    private static boolean implicitDdl(String engine) { return engine.equals("mysql") || engine.equals("oracle"); }
}
