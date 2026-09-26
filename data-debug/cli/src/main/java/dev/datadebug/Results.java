package dev.datadebug;

import java.io.*;
import java.sql.*;
import java.util.Set;

final class Results {
    static final int CELL_LIMIT = 4096, COLUMN_LIMIT = 256;
    private static final Set<Integer> BINARY = Set.of(Types.BINARY, Types.VARBINARY, Types.LONGVARBINARY, Types.BLOB);
    private static final Set<Integer> UNSUPPORTED = Set.of(Types.JAVA_OBJECT, Types.OTHER, Types.ARRAY, Types.STRUCT, Types.REF, Types.SQLXML);
    private static final Set<Integer> SCALAR = Set.of(Types.BOOLEAN, Types.BIT, Types.TINYINT, Types.SMALLINT, Types.INTEGER, Types.BIGINT, Types.FLOAT, Types.REAL, Types.DOUBLE, Types.NUMERIC, Types.DECIMAL, Types.DATE, Types.TIME, Types.TIMESTAMP, Types.TIME_WITH_TIMEZONE, Types.TIMESTAMP_WITH_TIMEZONE, Types.NULL);
    private record Cell(String text, boolean truncated) {}

    static String read(ResultSet rs, int maxRows) throws SQLException, IOException, Failure {
        ResultSetMetaData md = rs.getMetaData(); int count = md.getColumnCount();
        if (count < 1 || count > COLUMN_LIMIT) throw new Failure("COLUMN_LIMIT");
        StringBuilder columns = new StringBuilder("["); boolean truncated = false;
        for (int i = 1; i <= count; i++) {
            if (i > 1) columns.append(',');
            String label = md.getColumnLabel(i), type = md.getColumnTypeName(i);
            if (label == null) label = "";
            if (type == null) type = "";
            if (Json.bytes(label) > CELL_LIMIT || Json.bytes(type) > 256) throw new Failure("COLUMN_LIMIT");
            columns.append("{\"label\":").append(Json.quote(label)).append(",\"type\":").append(Json.quote(type)).append('}');
        }
        columns.append(']');
        StringBuilder rows = new StringBuilder("["); int n = 0;
        // Reserve room for envelope, transaction, transport and truncation metadata.
        int used = Json.bytes(columns.toString()) + 4096;
        if (used > Json.OUTPUT_LIMIT) throw new Failure("COLUMN_LIMIT");
        while (rs.next()) {
            Execution.checkInterrupted();
            if (n == maxRows) { truncated = true; break; }
            StringBuilder row = new StringBuilder("[");
            for (int i = 1; i <= count; i++) {
                if (i > 1) row.append(',');
                Cell cell = cell(rs, i, md.getColumnType(i));
                row.append(cell.text() == null ? "null" : Json.quote(cell.text()));
                truncated |= cell.truncated();
            }
            row.append(']');
            int size = Json.bytes(row.toString()) + 1;
            if (used + size > Json.OUTPUT_LIMIT) { truncated = true; break; }
            if (n++ > 0) rows.append(',');
            rows.append(row); used += size;
        }
        rows.append(']');
        return "\"columns\":" + columns + ",\"rows\":" + rows + ",\"rowCount\":" + n + ",\"truncated\":" + truncated;
    }
    private static Cell cell(ResultSet rs, int index, int type) throws SQLException, IOException, Failure {
        if (BINARY.contains(type)) {
            // Detect binary null without getObject/getBytes materializing the whole value.
            try (InputStream in = rs.getBinaryStream(index)) {
                return in == null ? new Cell(null, false) : new Cell("[binary or unsupported value omitted]", true);
            }
        }
        if (UNSUPPORTED.contains(type)) return new Cell("[binary or unsupported value omitted]", true);
        Reader source;
        if (SCALAR.contains(type)) {
            // Standard scalar formats are bounded by their SQL type, not an arbitrary LOB.
            String value = rs.getString(index);
            source = value == null ? null : new StringReader(value);
        } else source = rs.getCharacterStream(index);
        if (source == null) return new Cell(null, false);
        try (PushbackReader reader = new PushbackReader(source, 1)) {
            StringBuilder text = new StringBuilder(); int bytes = 0, c;
            while ((c = reader.read()) != -1) {
                Execution.checkInterrupted();
                int point = c;
                if (Character.isHighSurrogate((char)c)) {
                    int next = reader.read();
                    if (next >= 0 && Character.isLowSurrogate((char)next)) point = Character.toCodePoint((char)c, (char)next);
                    else { point = 0xfffd; if (next >= 0) reader.unread(next); }
                } else if (Character.isLowSurrogate((char)c)) point = 0xfffd;
                int size = point < 0x80 ? 1 : point < 0x800 ? 2 : point < 0x10000 ? 3 : 4;
                if (bytes + size > CELL_LIMIT) return new Cell(text.toString(), true);
                text.appendCodePoint(point); bytes += size;
            }
            return new Cell(text.toString(), false);
        }
    }
}
