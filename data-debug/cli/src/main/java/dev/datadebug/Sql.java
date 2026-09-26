package dev.datadebug;

import java.util.*;

/** Conservative dialect lexer, not a SQL purity proof. Unknown constructs fail closed. */
final class Sql {
    record Checked(String text, boolean ddl) {}
    static Checked check(String text, String engine, boolean write) throws Failure {
        if (text.isBlank()) throw new Failure("SQL_EMPTY");
        List<String> words = new ArrayList<>();
        List<String> top = new ArrayList<>();
        int depth = 0; boolean ended = false;
        for (int i = 0; i < text.length();) {
            char c = text.charAt(i);
            if (Character.isWhitespace(c)) { i++; continue; }
            if (c == '-' && i + 1 < text.length() && text.charAt(i + 1) == '-') {
                // MySQL requires whitespace after --; reject ambiguous dialect forms.
                if (engine.equals("mysql") && i + 2 < text.length() && !Character.isWhitespace(text.charAt(i + 2))) throw new Failure("SQL_UNSUPPORTED");
                i = lineEnd(text, i + 2); continue;
            }
            if (c == '#' && engine.equals("mysql")) { i = lineEnd(text, i + 1); continue; }
            if (c == '/' && i + 1 < text.length() && text.charAt(i + 1) == '*') {
                int end = text.indexOf("*/", i + 2);
                if (end < 0 || text.substring(i + 2, end).contains("/*") ||
                    (i + 2 < text.length() && (text.charAt(i + 2) == '!' || text.charAt(i + 2) == '+'))) throw new Failure("SQL_UNSUPPORTED");
                i = end + 2; continue;
            }
            if (ended) throw new Failure("SQL_MULTIPLE");
            if (c == ';') { if (depth != 0) throw new Failure("SQL_MULTIPLE"); ended = true; i++; continue; }
            if (engine.equals("oracle") && (c == 'q' || c == 'Q') && i + 2 < text.length() && text.charAt(i + 1) == '\'') {
                char open = text.charAt(i + 2);
                char close = switch(open) { case '[' -> ']'; case '{' -> '}'; case '(' -> ')'; case '<' -> '>'; default -> open; };
                int end = text.indexOf("" + close + '\'', i + 3);
                if (end < 0) throw new Failure("SQL_SYNTAX");
                words.add("LITERAL"); i = end + 2; continue;
            }
            if (c == '$' && engine.equals("postgresql")) {
                int endTag = text.indexOf('$', i + 1);
                if (endTag >= 0 && text.substring(i + 1, endTag).matches("[A-Za-z_][A-Za-z0-9_]*|")) {
                    String tag = text.substring(i, endTag + 1); int end = text.indexOf(tag, endTag + 1);
                    if (end < 0) throw new Failure("SQL_SYNTAX");
                    words.add("LITERAL"); i = end + tag.length(); continue;
                }
            }
            if (c == '\'' || c == '"' || (c == '`' && engine.equals("mysql")) || (c == '[' && engine.equals("sqlserver"))) {
                char close = c == '[' ? ']' : c; i++; boolean closed = false;
                while (i < text.length()) {
                    char q = text.charAt(i++);
                    // SQL modes differ for escapes. Refuse rather than misparse the boundary.
                    if (q == '\\') throw new Failure("SQL_UNSUPPORTED");
                    if (q == close) {
                        if (i < text.length() && text.charAt(i) == close) { i++; continue; }
                        closed = true; break;
                    }
                }
                if (!closed) throw new Failure("SQL_SYNTAX");
                words.add("LITERAL"); continue;
            }
            if (c == '(') { depth++; i++; continue; }
            if (c == ')') { if (--depth < 0) throw new Failure("SQL_SYNTAX"); i++; continue; }
            if (Character.isLetter(c) || c == '_') {
                int start = i++;
                while (i < text.length() && (Character.isLetterOrDigit(text.charAt(i)) || "_$#".indexOf(text.charAt(i)) >= 0)) i++;
                String word = text.substring(start, i).toUpperCase(Locale.ROOT);
                words.add(word); if (depth == 0) top.add(word); continue;
            }
            if (Character.isDigit(c) || ",.=<>!+-*/%:|&?".indexOf(c) >= 0) { i++; continue; }
            throw new Failure("SQL_UNSUPPORTED");
        }
        if (depth != 0 || words.isEmpty()) throw new Failure("SQL_SYNTAX");
        String first = words.get(0);
        boolean ddl = Set.of("CREATE", "ALTER", "DROP", "TRUNCATE", "COMMENT", "RENAME", "GRANT", "REVOKE").contains(first);
        if (write) {
            // Transaction control, batches, procedural code and administration are not replay-safe.
            if (!ddl && !Set.of("INSERT", "UPDATE", "DELETE", "MERGE", "SELECT", "WITH").contains(first)) throw new Failure("SQL_UNSUPPORTED");
        } else {
            if (first.equals("SHOW")) {
                if (!Set.of("mysql", "postgresql").contains(engine) || words.size() < 2) throw new Failure("SQL_READ_ONLY");
                if (engine.equals("mysql") && !Set.of("DATABASES", "TABLES", "COLUMNS", "INDEX", "INDEXES", "VARIABLES", "STATUS").contains(words.get(1))) throw new Failure("SQL_READ_ONLY");
                if (engine.equals("postgresql") && words.size() != 2) throw new Failure("SQL_READ_ONLY");
            } else if (first.equals("EXPLAIN")) {
                if (!Set.of("postgresql", "mysql").contains(engine) || !words.contains("SELECT")) throw new Failure("SQL_READ_ONLY");
            } else if (!Set.of("SELECT", "WITH").contains(first) || !words.contains("SELECT")) throw new Failure("SQL_READ_ONLY");
            Set<String> unsafe = Set.of("INSERT", "UPDATE", "DELETE", "MERGE", "INTO", "CREATE", "ALTER", "DROP", "TRUNCATE", "CALL", "EXEC", "EXECUTE", "ANALYZE", "ANALYSE", "LOCK", "FOR", "COPY", "OUTFILE", "DUMPFILE", "NEXTVAL", "SETVAL", "OPENROWSET", "OPENQUERY", "DBLINK", "GO");
            if (words.stream().anyMatch(unsafe::contains)) throw new Failure("SQL_READ_ONLY");
            if (words.contains("WITH") && !first.equals("WITH") && !first.equals("EXPLAIN")) throw new Failure("SQL_UNSUPPORTED");
        }
        if (words.contains("GO")) throw new Failure("SQL_MULTIPLE");
        if (write && words.stream().anyMatch(Set.of("CALL", "EXEC", "EXECUTE", "BEGIN", "END", "DECLARE", "WHILE", "WAITFOR", "BACKUP", "SHUTDOWN", "LOAD", "MERGE", "THROW", "RAISERROR", "USE", "PRINT", "DBCC", "KILL", "RETURN", "GOTO", "IF")::contains)) throw new Failure("SQL_UNSUPPORTED");
        // SQL Server also permits batches without semicolons. Recognize only one outer operation.
        Set<String> operations = Set.of("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE", "GRANT", "REVOKE", "COMMENT", "RENAME", "SHOW", "EXPLAIN");
        String operation = null;
        for (int i = 0; i < top.size(); i++) {
            String token = top.get(i);
            if (!operations.contains(token)) continue;
            if (operation == null || operation.equals("EXPLAIN")) { operation = token; continue; }
            if (token.equals("SELECT") && operation.equals("SELECT") && i > 0 &&
                (Set.of("UNION", "INTERSECT", "EXCEPT").contains(top.get(i - 1)) ||
                 (top.get(i - 1).equals("ALL") && i > 1 && top.get(i - 2).equals("UNION")))) continue;
            if (token.equals("SELECT") && Set.of("INSERT", "CREATE").contains(operation) && i > 0 &&
                (top.get(i - 1).equals("AS") || operation.equals("INSERT"))) { operation = "SELECT"; continue; }
            throw new Failure("SQL_MULTIPLE");
        }
        long sets = top.stream().filter("SET"::equals).count();
        if (sets > 0 && (!"UPDATE".equals(operation) || sets != 1)) throw new Failure("SQL_MULTIPLE");
        if (operation == null) throw new Failure("SQL_UNSUPPORTED");
        return new Checked(text.strip(), ddl);
    }
    private static int lineEnd(String s, int start) { int n = s.indexOf('\n', start); return n < 0 ? s.length() : n + 1; }
}
