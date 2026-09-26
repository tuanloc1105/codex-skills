package dev.datadebug;

import java.nio.charset.StandardCharsets;

final class Json {
    static final int OUTPUT_LIMIT = 1024 * 1024;
    private Json() {}
    static String quote(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (c < 32 || Character.isSurrogate(c)) {
                        out.append(String.format("\\u%04x", (int)c));
                    } else out.append(c);
                }
            }
        }
        return out.append('"').toString();
    }
    static int bytes(String value) { return value.getBytes(StandardCharsets.UTF_8).length; }
}
