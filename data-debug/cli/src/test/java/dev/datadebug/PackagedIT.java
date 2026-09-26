package dev.datadebug;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.jar.*;
import static org.junit.jupiter.api.Assertions.*;

class PackagedIT {
    @TempDir Path cwd;
    record Run(int status, String out, String err) {}
    Run jar(String... args) throws Exception {
        Path jar = Path.of("target/data-debug.jar").toAbsolutePath();
        List<String> command = new ArrayList<>(List.of(Path.of(System.getProperty("java.home"), "bin", "java").toString(), "-jar", jar.toString()));
        command.addAll(List.of(args));
        Path stdout=cwd.resolve("stdout"), stderr=cwd.resolve("stderr");
        Process p=new ProcessBuilder(command).directory(cwd.toFile()).redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();
        p.getOutputStream().close();
        if (!p.waitFor(15,TimeUnit.SECONDS)) { p.destroyForcibly(); fail("Packaged invocation timed out"); }
        return new Run(p.exitValue(), Files.readString(stdout), Files.readString(stderr));
    }
    @Test void packagedHelpAndDiscoveryFromDifferentCwd() throws Exception {
        for(String[] args:new String[][]{{},{"--help"},{"--version"}}) assertEquals(0,jar(args).status());
        Run drivers=jar("--drivers"); assertEquals(0,drivers.status()); assertEquals("",drivers.err());
        for(String driver:List.of("org.postgresql.Driver","oracle.jdbc.OracleDriver","com.mysql.cj.jdbc.Driver","com.microsoft.sqlserver.jdbc.SQLServerDriver")) assertTrue(drivers.out().contains(driver));
        Files.writeString(cwd.resolve(".env.db"), "HOST=localhost\nDATABASE=sample\nUSER=user\nPASSWORD=SENTINEL\n");
        Run keys=jar("--list-keys");assertEquals(0,keys.status());assertEquals("{\"keys\":[\"DATABASE\",\"HOST\",\"PASSWORD\",\"USER\"],\"duplicateKeys\":[]}\n",keys.out());
        Run config=jar("--check-config","--engine","postgresql","--host-key","HOST","--database-key","DATABASE","--user-key","USER","--password-key","PASSWORD");
        assertEquals(0,config.status());assertEquals("{\"valid\":true,\"engine\":\"postgresql\"}\n",config.out());
        assertFalse((keys.out()+keys.err()+config.out()+config.err()).contains("SENTINEL"));
    }
    @Test void packagedErrorsArePrivateAndNoConnectionOnBadSql() throws Exception {
        Files.writeString(cwd.resolve(".env.db"), "PASSWORD='SENTINEL\n");
        Run bad=jar("--list-keys");assertEquals(2,bad.status());assertEquals("",bad.out());assertTrue(bad.err().contains("CONFIG_SYNTAX"));assertFalse(bad.err().contains("SENTINEL"));
        Files.writeString(cwd.resolve(".env.db"), "HOST=localhost\nDB=sample\nU=user\nP=SENTINEL\n");
        Run empty=jar("--engine","postgresql","--host-key","HOST","--database-key","DB","--user-key","U","--password-key","P");
        assertEquals(2,empty.status());assertTrue(empty.err().contains("SQL_EMPTY"));assertFalse(empty.err().contains("SENTINEL"));
        Files.writeString(cwd.resolve(".env.db"), "HOST=localhost\nHOST=localhost\nDB=sample\nU=user\nP=SENTINEL\n");
        Run duplicate=jar("--check-config","--engine","postgresql","--host-key","HOST","--database-key","DB","--user-key","U","--password-key","P");
        assertEquals(2,duplicate.status());assertTrue(duplicate.err().contains("DUPLICATE_KEY"));assertFalse(duplicate.err().contains("SENTINEL"));
    }
    @Test void packageResourcesAndJava17Bytecode() throws Exception {
        try(JarFile jar=new JarFile("target/data-debug.jar")) {
            assertEquals("dev.datadebug.Main",jar.getManifest().getMainAttributes().getValue("Main-Class"));
            assertNotNull(jar.getEntry("META-INF/services/java.sql.Driver"));
            for(String cls:jar.stream().map(JarEntry::getName).filter(n -> n.endsWith(".class") && !n.startsWith("META-INF/versions/")).toList()) {
                try(DataInputStream in=new DataInputStream(jar.getInputStream(jar.getEntry(cls)))) {
                    assertEquals(0xCAFEBABE,in.readInt());in.readUnsignedShort();assertTrue(in.readUnsignedShort()<=61,cls);
                }
            }
            for (String notice : List.of("microsoft/LICENSE", "postgresql-42.7.13-jar/META-INF/LICENSE", "mysql-connector-j-9.7.0-jar/LICENSE", "ojdbc17-23.26.3.0.0-jar/META-INF/license.txt")) assertNotNull(jar.getEntry("META-INF/dependency-notices/" + notice), notice);
            assertFalse(jar.stream().anyMatch(e->e.getName().endsWith(".SF") || e.getName().endsWith(".RSA")));
        }
    }
}
