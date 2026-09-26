package dev.datadebug;

import java.io.*;
import java.nio.*;
import java.nio.charset.*;
import java.nio.file.*;
import java.util.*;

final class Config {
    static final int INPUT_LIMIT = 1024 * 1024;
    private final Map<String, String> values = new TreeMap<>();
    private final Set<String> duplicates = new HashSet<>();
    static String read(InputStream input) throws IOException, Failure {
        byte[] b = input.readNBytes(INPUT_LIMIT + 1);
        if (b.length > INPUT_LIMIT) throw new Failure("INPUT_LIMIT");
        try { return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(b)).toString(); }
        catch (CharacterCodingException e) { throw new Failure("UTF8"); }
    }
    static Config load(Path cwd) throws IOException, Failure {
        Path file = cwd.resolve(".env.db");
        if (!Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS)) throw new Failure("CONFIG_FILE");
        try (InputStream in = Files.newInputStream(file, LinkOption.NOFOLLOW_LINKS)) { return parse(read(in)); }
    }
    static Config parse(String text) throws Failure {
        Config c = new Config();
        for (String raw : text.split("\\R", -1)) {
            String line = raw.strip();
            if (line.isEmpty() || line.startsWith("#")) continue;
            if (line.startsWith("export ")) line = line.substring(7).stripLeading();
            int eq = line.indexOf('=');
            if (eq < 1) throw new Failure("CONFIG_SYNTAX");
            String key = line.substring(0, eq).strip();
            if (!key.matches("[A-Za-z_][A-Za-z0-9_]{0,127}")) throw new Failure("CONFIG_SYNTAX");
            String v = line.substring(eq + 1).strip();
            if (v.startsWith("\"") || v.startsWith("'")) {
                char q = v.charAt(0); int end = v.indexOf(q, 1);
                if (end < 0) throw new Failure("CONFIG_SYNTAX");
                String tail = v.substring(end + 1).strip();
                if (!tail.isEmpty() && !tail.startsWith("#")) throw new Failure("CONFIG_SYNTAX");
                v = v.substring(1, end); // Literal: no escaping, interpolation, or shell evaluation.
            } else {
                for (int i = 0; i < v.length(); i++) {
                    if (v.charAt(i) == '#' && (i == 0 || Character.isWhitespace(v.charAt(i - 1)))) { v = v.substring(0, i).stripTrailing(); break; }
                }
            }
            if (c.values.putIfAbsent(key, v) != null) c.duplicates.add(key);
        }
        return c;
    }
    String required(String key, boolean allowEmpty) throws Failure {
        if (duplicates.contains(key)) throw new Failure("DUPLICATE_KEY");
        String v = values.get(key);
        if (v == null || (!allowEmpty && v.isBlank())) throw new Failure("MISSING_KEY");
        return v;
    }
    String names() throws Failure {
        String output = "{\"keys\":[" + String.join(",", values.keySet().stream().map(Json::quote).toList()) +
            "],\"duplicateKeys\":[" + String.join(",", duplicates.stream().sorted().map(Json::quote).toList()) + "]}";
        if (Json.bytes(output) > Json.OUTPUT_LIMIT) throw new Failure("OUTPUT_LIMIT");
        return output;
    }
}
