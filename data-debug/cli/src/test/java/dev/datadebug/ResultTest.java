package dev.datadebug;

import org.junit.jupiter.api.Test;
import java.io.*;
import java.sql.*;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;

class ResultTest {
    ResultSet rows(int type, String value, int columns) {
        AtomicInteger row=new AtomicInteger();
        return JdbcTest.proxy(ResultSet.class,(n,a)->switch(n) {
            case "next"->row.incrementAndGet()==1;
            case "getString"->value;
            case "getCharacterStream"->{if(type==Types.INTEGER)fail("Scalar must not use character stream");yield value==null?null:new StringReader(value);}
            case "getBinaryStream"->value==null?null:new ByteArrayInputStream(new byte[]{1});
            case "getObject", "getBytes"->throw new AssertionError("Must not materialize arbitrary objects/binary");
            case "getMetaData"->JdbcTest.proxy(ResultSetMetaData.class,(x,y)->switch(x) {
                case "getColumnCount"->columns;case "getColumnLabel"->"x";case "getColumnTypeName"->"type";case "getColumnType"->type;default->null;
            }); default->null;
        });
    }
    @Test void scalarBinaryAndNull() throws Exception {
        assertTrue(Results.read(rows(Types.INTEGER,"123",1),100).contains("\"123\""));
        assertTrue(Results.read(rows(Types.BLOB,"secret",1),100).contains("omitted"));
        assertTrue(Results.read(rows(Types.BLOB,null,1),100).contains("[[null]]"));
        assertTrue(Results.read(rows(Types.ARRAY,"secret",1),100).contains("omitted"));
        assertThrows(Failure.class,()->Results.read(rows(Types.INTEGER,"1",257),100));
    }
    @Test void unicodeLobBoundary() throws Exception {
        String value="a".repeat(4093)+"😀"+"z";
        String s=Results.read(rows(Types.CLOB,value,1),100);
        assertTrue(s.contains("\"truncated\":true")); assertFalse(s.contains("\\ud83d"));
        s=Results.read(rows(Types.CLOB,"😀".repeat(1024),1),100);
        assertTrue(s.contains("\"truncated\":false")); assertTrue(s.contains("\\ud83d\\ude00"));
        s=Results.read(rows(Types.CLOB,"\\\"\n".repeat(5000),1),100);
        assertTrue(s.contains("\"truncated\":true")); assertTrue(Json.bytes(s)<Json.OUTPUT_LIMIT);
    }
}
