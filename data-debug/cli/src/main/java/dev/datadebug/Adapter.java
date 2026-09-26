package dev.datadebug;

import java.sql.*;
import java.util.*;
import java.util.regex.*;
import javax.net.ssl.*;
import java.security.cert.X509Certificate;
import oracle.jdbc.datasource.impl.OracleDataSource;

final class Adapter {
    record Target(String engine, String host, int port, String database, boolean sid, String user, String password) {
        @Override public String toString() { return "Target[redacted]"; }
    }
    record Request(Target target, String url, Properties properties, String tls) {
        @Override public String toString() { return "Request[redacted]"; }
    }
    private static final String HOST = "(?:[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?|\\[[0-9A-Fa-f:]+\\])";
    private static final String DATABASE = "[A-Za-z0-9_$#.-]{1,128}";
    static Target target(Options o, Map<String, String> f) throws Failure {
        String host, db, port; boolean sid = f.containsKey("sid");
        if (f.containsKey("url")) {
            // Endpoint-only URLs: no query/options, credentials, multi-host, descriptors or file paths.
            String pattern = switch(o.engine) {
                case "postgresql", "mysql" -> "jdbc:" + o.engine + "://(" + HOST + "):(\\d{1,5})/(" + DATABASE + ")";
                case "sqlserver" -> "jdbc:sqlserver://(" + HOST + "):(\\d{1,5});databaseName=(" + DATABASE + ")";
                case "oracle" -> "jdbc:oracle:thin:@(?:(?:tcps|tcp)://|//)(" + HOST + "):(\\d{1,5})/(" + DATABASE + ")";
                default -> throw new Failure("ARGUMENTS");
            };
            Matcher m = Pattern.compile(pattern).matcher(f.get("url"));
            if (!m.matches()) throw new Failure("URL_POLICY");
            host = m.group(1); port = m.group(2); db = m.group(3);
        } else {
            host = f.get("host"); db = f.getOrDefault("database", f.getOrDefault("service", f.get("sid")));
            port = f.getOrDefault("port", switch(o.engine) { case "postgresql" -> "5432"; case "mysql" -> "3306"; case "sqlserver" -> "1433"; default -> "1521"; });
        }
        if (host == null || !host.matches(HOST) || db == null || !db.matches(DATABASE)) throw new Failure("TARGET_FORMAT");
        return new Target(o.engine, host, Options.number(port, 65535), db, sid, f.get("user"), f.get("password"));
    }
    static Request request(Target t, Options o, String tls) {
        boolean plain = tls.equals("plaintext"), verified = tls.equals("verified");
        Properties p = new Properties(); p.setProperty("user", t.user); p.setProperty("password", t.password);
        String url;
        switch(t.engine) {
            case "postgresql" -> {
                url = "jdbc:postgresql://" + t.host + ":" + t.port + "/" + t.database;
                p.setProperty("sslmode", plain ? "disable" : verified ? "verify-full" : "require");
                p.setProperty("connectTimeout", "" + o.timeout); p.setProperty("socketTimeout", "" + o.timeout);
                p.setProperty("loginTimeout", "" + o.timeout); p.setProperty("readOnlyMode", "transaction");
            }
            case "mysql" -> {
                url = "jdbc:mysql://" + t.host + ":" + t.port + "/" + t.database;
                p.setProperty("sslMode", plain ? "DISABLED" : verified ? "VERIFY_IDENTITY" : "REQUIRED");
                p.setProperty("connectTimeout", "" + o.timeout * 1000); p.setProperty("socketTimeout", "" + o.timeout * 1000);
                p.setProperty("allowMultiQueries", "false"); p.setProperty("allowLoadLocalInfile", "false");
                p.setProperty("autoReconnect", "false"); p.setProperty("readOnlyPropagatesToServer", "true");
                p.setProperty("allowPublicKeyRetrieval", "false");
            }
            case "sqlserver" -> {
                url = "jdbc:sqlserver://" + t.host + ":" + t.port;
                p.setProperty("databaseName", t.database); p.setProperty("encrypt", plain ? "false" : "true");
                p.setProperty("trustServerCertificate", verified ? "false" : "true");
                p.setProperty("loginTimeout", "" + o.timeout); p.setProperty("socketTimeout", "" + o.timeout * 1000);
                p.setProperty("connectRetryCount", "0"); p.setProperty("responseBuffering", "adaptive");
                p.setProperty("applicationIntent", o.mode.equals("read") ? "ReadOnly" : "ReadWrite");
            }
            default -> {
                url = "jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS=(PROTOCOL=" + (plain ? "TCP" : "TCPS") + ")(HOST=" + t.host + ")(PORT=" + t.port + "))(CONNECT_DATA=(" + (t.sid ? "SID" : "SERVICE_NAME") + "=" + t.database + ")))";
                p.setProperty("oracle.net.ssl_server_dn_match", "" + verified);
                p.setProperty("oracle.net.CONNECT_TIMEOUT", "" + o.timeout * 1000);
                p.setProperty("oracle.net.OUTBOUND_CONNECT_TIMEOUT", "" + o.timeout * 1000);
                p.setProperty("oracle.jdbc.ReadTimeout", "" + o.timeout * 1000);
                p.setProperty("oracle.jdbc.enableACSupport", "false");
            }
        }
        return new Request(t, url, p, tls);
    }
    static Connection connect(Request r) throws SQLException {
        if (!r.target.engine.equals("oracle")) return DriverManager.getConnection(r.url, r.properties);
        OracleDataSource ds = new OracleDataSource(); ds.setURL(r.url); ds.setConnectionProperties(r.properties);
        if (r.tls.equals("relaxed")) ds.setSSLContext(relaxedContext());
        return ds.getConnection();
    }
    static SSLContext relaxedContext() throws SQLException {
        try {
            SSLContext context = SSLContext.getInstance("TLS");
            context.init(null, new TrustManager[]{new X509TrustManager() {
                public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
                public void checkClientTrusted(X509Certificate[] chain, String auth) { }
                public void checkServerTrusted(X509Certificate[] chain, String auth) { }
            }}, null);
            return context;
        } catch (java.security.GeneralSecurityException e) { throw new SQLException("TLS setup unavailable"); }
    }
    static boolean certificateFailure(Throwable error) {
        Set<Throwable> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        for (Throwable e = error; e != null && seen.add(e); e = e.getCause()) {
            if (e instanceof java.security.cert.CertificateException || e instanceof java.security.cert.CertPathValidatorException || e instanceof java.security.cert.CertPathBuilderException) return true;
            // Some vendors discard the typed cause. Restrict textual matching to certificate diagnostics.
            String m = e.getMessage();
            if (m != null && (m.contains("PKIX path building failed") || m.contains("No subject alternative") || m.contains("No name matching") || m.contains("server certificate does not match") || m.contains("could not be verified by hostnameverifier") || m.contains("Failed to validate the server name in a certificate") || m.contains("ORA-29024") || m.contains("ORA-17965"))) return true;
        }
        return false;
    }
    static String errorCode(SQLException e) {
        String state = e.getSQLState();
        if (state != null && state.startsWith("28")) return "AUTHENTICATION";
        if (e instanceof SQLTimeoutException) return "TIMEOUT";
        if (certificateFailure(e)) return "TLS_CERTIFICATE";
        if (state != null && state.startsWith("08")) return "CONNECTION";
        return "DATABASE";
    }
}
