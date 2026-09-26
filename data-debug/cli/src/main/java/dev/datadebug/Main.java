package dev.datadebug;

import java.io.*;
import java.nio.file.Path;
import java.util.logging.*;

public final class Main {
    private Main() {}
    public static void main(String[] args) {
        // Drivers must not publish raw connection values through JUL or inherited log handlers.
        LogManager.getLogManager().reset();
        Logger.getLogger("").setLevel(Level.OFF);
        int status = run(args, Path.of(""), System.in, System.out, System.err);
        if (status != 0) System.exit(status);
    }
    static int run(String[] args, Path cwd, InputStream in, PrintStream out, PrintStream err) {
        try {
            Options o = Options.parse(args);
            if (o.command.equals("help")) {
                out.println("Data Debug: java -jar /absolute/skill/cli/target/data-debug.jar [options]\n" +
                    "--help | --version | --list-keys | --check-config | --drivers\n" +
                    "--engine postgresql|mysql|oracle|sqlserver\n" +
                    "--host-key NAME [--port-key NAME] --database-key NAME\n" +
                    "Oracle: --service-key NAME or --sid-key NAME instead of --database-key\n" +
                    "Alternatively: --url-key NAME (restricted endpoint-only JDBC URL)\n" +
                    "--user-key NAME --password-key NAME\n" +
                    "--mode read|write --tls verified|relaxed|plaintext --max-rows 1..10000 --timeout 1..300\n" +
                    "Reads only cwd/.env.db; SQL via UTF-8 stdin. Write requires exact user approval in the skill.");
            } else if (o.command.equals("version")) out.println("data-debug 1.0.0");
            else if (o.command.equals("drivers")) {
                out.println("{\"drivers\":[" + String.join(",", java.util.ServiceLoader.load(java.sql.Driver.class)
                    .stream().map(p -> Json.quote(p.type().getName())).sorted().toList()) + "]}");
            } else {
                Config c = Config.load(cwd);
                if (o.command.equals("list-keys")) out.println(c.names());
                else {
                    var fields = o.resolve(c);
                    Adapter.target(o, fields); // Validate endpoint policy without connecting.
                    if (o.command.equals("check-config")) out.println("{\"valid\":true,\"engine\":" + Json.quote(o.engine) + "}");
                    else out.println(Execution.run(o, fields, Config.read(in), Adapter::connect));
                }
            }
            return 0;
        } catch (Failure e) { err.println(e.json()); return 2;
        } catch (Exception | LinkageError e) { err.println("{\"error\":\"IO_OR_DRIVER\"}"); return 2; }
    }
}
