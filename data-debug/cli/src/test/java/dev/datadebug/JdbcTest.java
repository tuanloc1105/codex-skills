package dev.datadebug;

import org.junit.jupiter.api.Test;
import java.io.*;
import java.lang.reflect.*;
import java.sql.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.security.cert.CertificateException;
import static org.junit.jupiter.api.Assertions.*;

class JdbcTest {
    static Options options(String engine, boolean write) throws Failure {
        Options o = Options.parse(new String[]{"--engine", engine, "--mode", write ? "write" : "read"}); return o;
    }
    static Map<String,String> fields(String engine) {
        return Map.of("host", "localhost", engine.equals("oracle") ? "service" : "database", "sample", "user", "user", "password", "SENTINEL");
    }
    @Test void fourAdaptersAndUrlPolicy() throws Exception {
        for (String engine : List.of("postgresql", "mysql", "sqlserver", "oracle")) {
            Options o = options(engine, false); var t = Adapter.target(o, fields(engine));
            Adapter.Request verified = Adapter.request(t,o,"verified"), relaxed = Adapter.request(t,o,"relaxed"), plain = Adapter.request(t,o,"plaintext");
            assertEquals(t, relaxed.target()); assertEquals("SENTINEL", relaxed.properties().getProperty("password"));
            assertFalse(t.toString().contains("SENTINEL")); assertFalse(verified.toString().contains("SENTINEL"));
            switch(engine) {
                case "postgresql" -> { assertEquals("verify-full", verified.properties().getProperty("sslmode")); assertEquals("require", relaxed.properties().getProperty("sslmode")); }
                case "mysql" -> { assertEquals("VERIFY_IDENTITY", verified.properties().getProperty("sslMode")); assertEquals("REQUIRED", relaxed.properties().getProperty("sslMode")); assertEquals("false", relaxed.properties().getProperty("autoReconnect")); }
                case "sqlserver" -> { assertEquals("true", relaxed.properties().getProperty("encrypt")); assertEquals("true", relaxed.properties().getProperty("trustServerCertificate")); assertEquals("0", plain.properties().getProperty("connectRetryCount")); }
                case "oracle" -> { assertTrue(relaxed.url().contains("PROTOCOL=TCPS")); assertTrue(plain.url().contains("PROTOCOL=TCP")); assertNotNull(Adapter.relaxedContext()); }
            }
        }
        Options pg = options("postgresql", false);
        for (String bad : List.of("jdbc:postgresql://host:5432/db?sslmode=disable", "jdbc:postgresql://user:pw@host:5432/db", "jdbc:postgresql://host,other:5432/db", "jdbc:postgresql://host:5432/db%3foptions")) {
            assertThrows(Failure.class, () -> Adapter.target(pg, Map.of("url",bad,"user","u","password","SENTINEL")));
        }
        assertEquals("db", Adapter.target(pg, Map.of("url","jdbc:postgresql://host:5432/db","user","u","password","p")).database());
        var sid = new HashMap<>(fields("oracle")); sid.remove("service");sid.put("sid","XE");
        assertTrue(Adapter.request(Adapter.target(options("oracle", false), sid),options("oracle", false),"verified").url().contains("(SID=XE)"));
    }
    @Test void dialectClassifier() throws Exception {
        for (String engine : List.of("postgresql", "mysql", "sqlserver", "oracle")) {
            for (String sql : List.of("SELECT 'a;DELETE x' AS x; -- end", "/* comment */ WITH x AS (SELECT 1 AS n) SELECT n FROM x", "SELECT 1 UNION ALL SELECT 2", "SELECT (SELECT 1)")) assertNotNull(Sql.check(sql,engine,false));
            for (String sql : List.of("SELECT 1; DELETE FROM x", "SELECT 1 DELETE FROM x", "UPDATE x SET n=1 UPDATE y SET n=2", "WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x", "SELECT * INTO backup FROM t", "SELECT * FROM t FOR UPDATE", "EXPLAIN ANALYZE SELECT 1", "CALL x()", "SELECT 'unterminated", "SELECT 1 /* unfinished", "SELECT nextval('s')", "SELECT 1; SELECT 2", "SELECT 1 GO SELECT 2", "(SELECT 1)")) assertThrows(Failure.class, () -> Sql.check(sql,engine,false), sql);
            assertThrows(Failure.class, () -> Sql.check("UPDATE x SET n=1 DELETE FROM y",engine,true));
            assertNotNull(Sql.check("UPDATE x SET n=(SELECT 1)",engine,true));
            for (String batch : List.of("UPDATE x SET n=1 THROW 50000, 'x', 1", "UPDATE x SET n=1 SET IDENTITY_INSERT x ON", "SELECT 1 PRINT 'x'")) assertThrows(Failure.class, () -> Sql.check(batch,engine,true));
        }
        assertNotNull(Sql.check("SELECT $$;DELETE x$$", "postgresql", false));
        assertNotNull(Sql.check("SELECT q'[x; DELETE FROM t]' FROM dual", "oracle", false));
        assertNotNull(Sql.check("SELECT [a;b] FROM [t]", "sqlserver", false));
        assertNotNull(Sql.check("SHOW TABLES", "mysql", false));
        assertNotNull(Sql.check("EXPLAIN SELECT 1", "postgresql", false));
        assertThrows(Failure.class, () -> Sql.check("SELECT 1 /*! INTO OUTFILE 'x' */", "mysql", false));
        assertThrows(Failure.class, () -> Sql.check("SELECT 'x\\'; DELETE FROM t", "mysql", false));
    }
    @Test void tlsFallbackExecutesOnceAndNeverReplays() throws Exception {
        for (String engine : List.of("postgresql","mysql","sqlserver","oracle")) {
            Fake f = new Fake(); AtomicInteger attempts = new AtomicInteger(); List<Adapter.Request> requests = new ArrayList<>();
            String output = Execution.run(options(engine,false),fields(engine),"SELECT 1", r -> {
                requests.add(r); if (attempts.incrementAndGet()==1) throw new SQLException("secret SENTINEL", "08001", new CertificateException("SENTINEL"));
                assertEquals(0, f.executes); return f.connection();
            });
            assertEquals(2,attempts.get()); assertEquals(1,f.executes); assertEquals(1,f.rollbacks); assertTrue(output.contains("relaxed-encrypted")); assertFalse(output.contains("SENTINEL"));
            assertEquals(requests.get(0).target(),requests.get(1).target());
            Fake failed = new Fake(); failed.failExecute=true; attempts.set(0);
            Failure e=assertThrows(Failure.class,()-> Execution.run(options(engine,true), fields(engine),"UPDATE t SET n=1", r->{attempts.incrementAndGet();return failed.connection();}));
            assertEquals(1,attempts.get());assertEquals(1,failed.executes);assertEquals(1,failed.rollbacks);assertFalse(e.json().contains("SENTINEL"));
        }
    }
    @Test void authAndNetworkNeverDowngrade() throws Exception {
        for (String state : List.of("28000","08001")) {
            AtomicInteger attempts=new AtomicInteger();
            assertThrows(Failure.class,()->Execution.run(options("mysql",false),fields("mysql"),"SELECT 1",r->{attempts.incrementAndGet();throw new SQLException("SENTINEL",state);}));
            assertEquals(1,attempts.get());
        }
    }
    @Test void transactionsDdlAndCommitUncertainty() throws Exception {
        Fake f=new Fake();String result=Execution.run(options("mysql",true),fields("mysql"),"CREATE TABLE t (n int)",r->f.connection());
        assertEquals(1,f.commits);assertTrue(result.contains("ddl-may-auto-commit"));assertFalse(f.readOnly);
        Fake bad=new Fake();bad.failExecute=true;
        Failure e=assertThrows(Failure.class,()->Execution.run(options("oracle",true),fields("oracle"),"DROP TABLE t",r->bad.connection()));
        assertEquals("ddl-may-have-auto-committed",e.transaction);
        Fake commit=new Fake();commit.failCommit=true;
        e=assertThrows(Failure.class,()->Execution.run(options("postgresql",true),fields("postgresql"),"UPDATE t SET n=1",r->commit.connection()));
        assertEquals("commit-unknown",e.transaction);assertEquals(0,commit.rollbacks);
    }
    @Test void boundedResultsPreserveNullDuplicateLabelsAndTypes() throws Exception {
        Fake f=new Fake();f.results=true;f.rowTotal=3;f.cell="x".repeat(9000);
        Options o=options("postgresql",false);o.rows=2;
        String s=Execution.run(o,fields("postgresql"),"SELECT 1",r->f.connection());
        assertTrue(s.contains("\"rowCount\":2"));assertTrue(s.contains("\"truncated\":true"));assertTrue(s.contains(",null]"));
        assertEquals(2, s.split("\\\"label\\\":\\\"same\\\"",-1).length - 1);
        assertTrue(Json.bytes(s)<Json.OUTPUT_LIMIT);assertFalse(s.contains("x".repeat(4097)));
        Fake huge=new Fake();huge.results=true;huge.rowTotal=10000;huge.cell="é".repeat(4000);o.rows=10000;
        s=Execution.run(o,fields("postgresql"),"SELECT 1",r->huge.connection()); assertTrue(Json.bytes(s)<Json.OUTPUT_LIMIT);assertTrue(s.contains("\"truncated\":true"));
    }
    @Test void timeoutCannotExecuteAfterLateConnection() throws Exception {
        Options o=options("postgresql",true);o.timeout=1;Fake f=new Fake();
        Failure e=assertThrows(Failure.class,()->Execution.run(o,fields("postgresql"),"UPDATE t SET n=1",r->{
            try { Thread.sleep(1800); } catch (InterruptedException x) { /* Simulate a driver consuming the interrupt. */ }
            return f.connection();
        }));
        assertEquals("TIMEOUT",e.code);assertEquals(0,f.executes);
    }
    @Test void writeCertificateFallbackAndBoundedRetries() throws Exception {
        for(String engine:List.of("postgresql","mysql","sqlserver","oracle")) {
            AtomicInteger attempts=new AtomicInteger();Fake f=new Fake();
            String output=Execution.run(options(engine,true),fields(engine),"UPDATE t SET n=1",r->{
                if(attempts.incrementAndGet()==1)throw new SQLException("SENTINEL","08001",new CertificateException("SENTINEL"));
                return f.connection();
            });
            assertEquals(2,attempts.get());assertEquals(1,f.executes);assertEquals(1,f.commits);assertTrue(output.contains("relaxed-encrypted"));
            attempts.set(0);
            assertThrows(Failure.class,()->Execution.run(options(engine,true),fields(engine),"UPDATE t SET n=1",r->{attempts.incrementAndGet();throw new SQLException("SENTINEL","08001",new CertificateException("SENTINEL"));}));
            assertEquals(2,attempts.get());
        }
    }
    @Test void hostnameOnlyVendorDiagnosticsRetryWithoutLeakage() throws Exception {
        for(String diagnostic:List.of("The hostname SENTINEL could not be verified by hostnameverifier org.postgresql.ssl.PGjdbcHostnameVerifier.","ORA-17965: Host name SENTINEL does not match CN/SAN", "Failed to validate the server name in a certificate SENTINEL")) {
            AtomicInteger attempts=new AtomicInteger();Fake f=new Fake();
            String output=Execution.run(options("postgresql",false),fields("postgresql"),"SELECT 1",r->{
                if(attempts.incrementAndGet()==1)throw new SQLException(diagnostic,"08001");return f.connection();
            });
            assertEquals(2,attempts.get());assertEquals(1,f.executes);assertFalse(output.contains("SENTINEL"));
        }
        assertFalse(Adapter.certificateFailure(new javax.net.ssl.SSLHandshakeException("protocol_version")));
    }
    interface Invoke { Object call(String name,Object[] args) throws Throwable; }
    @SuppressWarnings("unchecked") static <T> T proxy(Class<T> type, Invoke invoke) {
        return (T)Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},(p,m,a)->{
            Object v=invoke.call(m.getName(),a==null?new Object[0]:a);
            if(v!=null)return v;
            if(m.getReturnType()==boolean.class)return false;
            if(m.getReturnType()==int.class)return 0;
            if(m.getReturnType()==long.class)return 0L;
            return null;
        });
    }
    static class Fake {
        int executes, commits, rollbacks, controls, rowTotal=1;boolean readOnly,failExecute,failCommit,results;
        String cell="ok";
        Connection connection() {
            return proxy(Connection.class,(n,a)->switch(n){
                case "setReadOnly"->{readOnly=(boolean)a[0];yield null;}
                case "commit"->{commits++;if(failCommit)throw new SQLException("SENTINEL");yield null;}
                case "rollback"->{rollbacks++;yield null;}
                case "getMetaData"->proxy(DatabaseMetaData.class,(x,y)->x.equals("getDatabaseMajorVersion")?12:null);
                case "createStatement"->statement(); default->null;
            });
        }
        Statement statement() {
            return proxy(Statement.class,(n,a)->switch(n){
                case "execute"->{if(a[0].equals("SET TRANSACTION READ ONLY")){controls++;yield false;}executes++;if(failExecute)throw new SQLException("SENTINEL");yield results;}
                case "getLargeUpdateCount"->1L; case "getResultSet"->resultSet(); default->null;
            });
        }
        ResultSet resultSet() {
            AtomicInteger row=new AtomicInteger();
            return proxy(ResultSet.class,(n,a)->switch(n){
                case "next"->row.incrementAndGet()<=rowTotal;
                case "getCharacterStream"->(int)a[0]==2?null:new StringReader(cell);
                case "getMetaData"->proxy(ResultSetMetaData.class,(x,y)->switch(x){
                    case "getColumnCount"->2;case "getColumnLabel"->"same";case "getColumnTypeName"->"VARCHAR";case "getColumnType"->Types.VARCHAR;default->null;
                }); default->null;
            });
        }
    }
}
