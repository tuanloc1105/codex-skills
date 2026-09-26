package dev.datadebug;

import java.util.*;

final class Options {
    static final Set<String> FIELDS = Set.of("host", "port", "database", "user", "password", "service", "sid", "url");
    final Map<String, String> keys = new TreeMap<>();
    String engine, command = "query", mode = "read", tls = "verified";
    int rows = 100, timeout = 10;

    static Options parse(String[] args) throws Failure {
        Options o = new Options();
        if (args.length == 0) { o.command = "help"; return o; }
        Set<String> seen = new HashSet<>();
        for (int i = 0; i < args.length; i++) {
            String a = args[i];
            if (!seen.add(a)) throw new Failure("ARGUMENTS");
            if (Set.of("--help", "--version", "--list-keys", "--check-config", "--drivers").contains(a)) {
                if (!o.command.equals("query")) throw new Failure("ARGUMENTS");
                o.command = a.substring(2); continue;
            }
            if (++i == args.length) throw new Failure("ARGUMENTS");
            String v = args[i];
            if (a.startsWith("--") && a.endsWith("-key")) {
                String f = a.substring(2, a.length() - 4);
                if (!FIELDS.contains(f) || !v.matches("[A-Za-z_][A-Za-z0-9_]{0,127}")) throw new Failure("ARGUMENTS");
                o.keys.put(f, v);
            } else switch (a) {
                case "--engine" -> o.engine = v;
                case "--mode" -> o.mode = v;
                case "--tls" -> o.tls = v;
                case "--max-rows" -> o.rows = number(v, 10000);
                case "--timeout" -> o.timeout = number(v, 300);
                default -> throw new Failure("ARGUMENTS");
            }
        }
        if (o.engine != null && !Set.of("postgresql", "mysql", "sqlserver", "oracle").contains(o.engine)) throw new Failure("ARGUMENTS");
        if (!Set.of("read", "write").contains(o.mode) || !Set.of("verified", "relaxed", "plaintext").contains(o.tls)) throw new Failure("ARGUMENTS");
        return o;
    }
    static int number(String v, int maximum) throws Failure {
        try { int n = Integer.parseInt(v); if (n > 0 && n <= maximum) return n; }
        catch (NumberFormatException ignored) { }
        throw new Failure("ARGUMENTS");
    }
    Map<String, String> resolve(Config c) throws Failure {
        if (engine == null || !keys.containsKey("user") || !keys.containsKey("password")) throw new Failure("MAPPING");
        boolean url = keys.containsKey("url");
        if (url && keys.keySet().stream().anyMatch(f -> !Set.of("url", "user", "password").contains(f))) throw new Failure("MAPPING");
        if (!url) {
            if (!keys.containsKey("host")) throw new Failure("MAPPING");
            if (engine.equals("oracle")) {
                if (keys.containsKey("database") || keys.containsKey("service") == keys.containsKey("sid")) throw new Failure("MAPPING");
            } else if (!keys.containsKey("database") || keys.containsKey("service") || keys.containsKey("sid")) throw new Failure("MAPPING");
        }
        if (new HashSet<>(keys.values()).size() != keys.size()) throw new Failure("MAPPING");
        Map<String, String> fields = new HashMap<>();
        for (var e : keys.entrySet()) fields.put(e.getKey(), c.required(e.getValue(), e.getKey().equals("password")));
        return fields;
    }
}
