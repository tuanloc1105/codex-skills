package dev.datadebug;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import java.io.*;
import static org.junit.jupiter.api.Assertions.*;

class CoreTest {
    @TempDir Path cwd;
    @Test void literalsAndNames() throws Exception {
        Config c = Config.parse(" A = 'secret # x' # comment\nB=\"$(not executed) ${A}\"\nC=\nD=raw#hash #comment\nA=again\n");
        assertEquals("$(not executed) ${A}", c.required("B", false));
        assertEquals("", c.required("C", true));
        assertEquals("raw#hash", c.required("D", false));
        assertEquals("DUPLICATE_KEY", assertThrows(Failure.class, () -> c.required("A", false)).code);
        assertEquals("{\"keys\":[\"A\",\"B\",\"C\",\"D\"],\"duplicateKeys\":[\"A\"]}", c.names());
        assertThrows(Failure.class, () -> c.required("absent", true));
    }
    @Test void malformedAndBounds() {
        for (String s : new String[]{"A='SENTINEL", "bad key=SENTINEL", "SENTINEL", "A='x' SENTINEL"}) {
            Failure e = assertThrows(Failure.class, () -> Config.parse(s)); assertFalse(e.getMessage().contains("SENTINEL"));
        }
        assertThrows(Failure.class, () -> Config.read(new ByteArrayInputStream(new byte[Config.INPUT_LIMIT + 1])));
        assertThrows(Failure.class, () -> Config.read(new ByteArrayInputStream(new byte[]{(byte)0xff})));
    }
    @Test void cliPrivacyAndCwd() throws Exception {
        Files.writeString(cwd.resolve(".env.db"), "PRIVATE=SENTINEL\n");
        ByteArrayOutputStream out = new ByteArrayOutputStream(), err = new ByteArrayOutputStream();
        assertEquals(0, Main.run(new String[]{"--list-keys"}, cwd, InputStream.nullInputStream(), new PrintStream(out), new PrintStream(err)));
        assertTrue(out.toString().contains("PRIVATE")); assertFalse(out.toString().contains("SENTINEL"));
        assertEquals(2, Main.run(new String[]{"--list-keys"}, cwd.resolve("other"), InputStream.nullInputStream(), new PrintStream(out), new PrintStream(err)));
        assertFalse(err.toString().contains(cwd.toString()));
        for (String[] a : new String[][]{{}, {"--help"}, {"--version"}}) assertEquals(0, Main.run(a, cwd.resolve("absent"), InputStream.nullInputStream(), new PrintStream(out), new PrintStream(err)));
    }
    @Test void argumentsAndMapping() throws Exception {
        for (String[] a : new String[][]{{"--password", "SENTINEL"}, {"--timeout", "0"}, {"--max-rows", "10001"}, {"--engine", "other"}, {"--help", "--version"}}) assertThrows(Failure.class, () -> Options.parse(a));
        Options o = Options.parse(new String[]{"--engine", "postgresql", "--host-key", "H", "--database-key", "D", "--user-key", "U", "--password-key", "P"});
        assertEquals("pw", o.resolve(Config.parse("H=host\nD=db\nU=user\nP=pw")).get("password"));
        o.keys.put("url", "URL"); assertThrows(Failure.class, () -> o.resolve(Config.parse("URL=x")));
    }
    @Test void oracleMappingsAndSymlinkConfig() throws Exception {
        Config c=Config.parse("H=localhost\nS=svc\nI=sid\nU=user\nP=pw");
        Options o=Options.parse(new String[]{"--engine","oracle","--host-key","H","--service-key","S","--sid-key","I","--user-key","U","--password-key","P"});
        assertThrows(Failure.class,()->o.resolve(c));
        o.keys.remove("sid");assertEquals("svc",o.resolve(c).get("service"));
        o.keys.put("password","U");assertThrows(Failure.class,()->o.resolve(c));
        Path real=cwd.resolve("literal");Files.writeString(real,"P=SENTINEL");
        Files.createSymbolicLink(cwd.resolve(".env.db"),real);
        assertEquals("CONFIG_FILE",assertThrows(Failure.class,()->Config.load(cwd)).code);
    }
}
