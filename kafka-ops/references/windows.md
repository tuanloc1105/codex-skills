# Vận hành Kafka trên native Windows

## Mục lục

- [Phạm vi hỗ trợ](#phạm-vi-hỗ-trợ)
- [Discovery trên Windows](#discovery-trên-windows)
- [Gọi guard từ PowerShell](#gọi-guard-từ-powershell)
- [Gọi Kafka CLI](#gọi-kafka-cli)
- [Hardening cho batch script](#hardening-cho-batch-script)
- [Checklist Windows](#checklist-windows)
- [Nguồn chính thức](#nguồn-chính-thức)

## Phạm vi hỗ trợ

Hỗ trợ Windows 10/11 và Windows Server bằng Windows PowerShell 5.1 hoặc PowerShell 7, với Apache Kafka CLI chính thức dạng `.bat` trong `bin\windows`. WSL được xem là Linux: dùng Kafka Linux distribution và `python3`, không gọi `.bat` qua `/mnt/c`.

Các prerequisite local:

- Apache Kafka CLI đã được cài/giải nén sẵn.
- Java phù hợp với bản Kafka; preflight xác minh gián tiếp bằng `kafka-topics --version`.
- Python 3.9+ để chạy policy guard.
- `powershell.exe` 5.1 hoặc `pwsh.exe` 7.

Nếu thiếu Kafka CLI, Java làm version check lỗi, hoặc không có Python phù hợp, dừng workflow. Không tự cài hay tải dependency.

## Discovery trên Windows

Khi không có `--kafka-bin`, guard tìm installation theo các nguồn sau rồi fail closed nếu có nhiều `kafka-topics` khác nhau:

1. `KAFKA_HOME\bin\windows`.
2. `KAFKA_HOME\bin` cho wrapper native đặc biệt nếu có.
3. Mọi thư mục trong `PATH`.

Chỉ truyền `--kafka-bin` khi người dùng đã chọn installation cụ thể; path phải absolute và thường là `C:\...\Kafka\bin\windows`. Guard nhận `.bat`, `.cmd`, `.exe` hoặc executable không extension trên native Windows; không nhận `.sh` trong PowerShell.

## Gọi guard từ PowerShell

Luôn chạy launcher như child process để exit code không kết thúc PowerShell session hiện tại. Chỉ dùng `-ExecutionPolicy Bypass` ở process này, không đổi policy `CurrentUser` hoặc `LocalMachine`.

```powershell
$skillRoot = 'C:\path\to\kafka-ops'
$guard = Join-Path -Path $skillRoot -ChildPath 'scripts\kafka_guard.ps1'
$guardHostArgs = @(
    '-NoLogo',
    '-NoProfile',
    '-NonInteractive',
    '-ExecutionPolicy', 'Bypass',
    '-File', $guard
)

& powershell.exe @guardHostArgs preflight --require kafka-topics
$guardExitCode = $LASTEXITCODE
if ($guardExitCode -ne 0) {
    throw "Kafka guard preflight blocked with exit code $guardExitCode"
}
```

Với PowerShell 7, thay `powershell.exe` bằng `pwsh.exe`. Launcher ưu tiên `py.exe -3`, sau đó `python.exe`, rồi `python3.exe`, từ chối Python thấp hơn 3.9, và ép UTF-8 để JSON/confirmation phrase không hỏng khi stdout bị redirect.

Giữ command dưới dạng một argv array. Ví dụ read-only:

```powershell
$binary = 'C:\Program Files\Kafka\bin\windows\kafka-topics.bat'
$kafkaArgv = @(
    $binary,
    '--describe',
    '--topic', 'orders',
    '--bootstrap-server', 'broker01.example:9092'
)

$unsupportedNativeToken = @($kafkaArgv | Where-Object {
    [string]::IsNullOrEmpty([string]$_) -or ([string]$_) -match '[\u0000-\u001F\u007F"]'
})
if ($unsupportedNativeToken.Count -gt 0) {
    throw 'Windows PowerShell cannot transport this exact argv losslessly; stop instead of escaping it.'
}

& powershell.exe @guardHostArgs classify -- @kafkaArgv
$classifyExitCode = $LASTEXITCODE
if ($classifyExitCode -ne 0) {
    throw "Kafka command is not automatically executable; guard exit code $classifyExitCode"
}
```

Không chuyển array thành một string. Nếu thay một token, chạy `classify` lại; với mutation còn phải tạo lại `plan` và so khớp change ID.

## Gọi Kafka CLI

`invoke_kafka.ps1` chỉ là transport an toàn cho exact argv trên Windows; nó không cấp quyền mutation và không thay thế classifier, plan hay xác nhận của người dùng. Runner:

- Chỉ nhận absolute Kafka executable đã tồn tại.
- Gọi `.bat`/`.cmd` bằng `cmd.exe /d /s /c`, quote từng token và kiểm tra exit code ngay lập tức.
- Gọi `.exe` trực tiếp bằng argument array.
- Không log argv hoặc đọc credential file.

```powershell
$runner = Join-Path -Path $skillRoot -ChildPath 'scripts\invoke_kafka.ps1'
$runnerHostArgs = @(
    '-NoLogo',
    '-NoProfile',
    '-NonInteractive',
    '-ExecutionPolicy', 'Bypass',
    '-File', $runner
)

& powershell.exe @runnerHostArgs @kafkaArgv
$kafkaExitCode = $LASTEXITCODE
if ($kafkaExitCode -ne 0) {
    throw "Kafka CLI failed with exit code $kafkaExitCode"
}
```

Đừng dùng `Start-Process -ArgumentList`, `Invoke-Expression`, `cmd /c` tự ghép, `--%`, pipeline hoặc redirection để thay runner.

## Hardening cho batch script

Mọi Windows transport đều từ chối empty token, embedded `"` và control character vì Windows PowerShell 5.1 không bảo toàn được các shape đó qua native boundary. Agent phải kiểm tra raw `$kafkaArgv` trước khi mở child process như ví dụ trên; guard và runner lặp lại check này theo kiểu defense-in-depth.

`.bat` và `.cmd` còn bị từ chối khi token chứa `%`, `!`, `^`, `&`, `|`, `<` hoặc `>`. Đây là fail-closed boundary chống expansion/injection của `cmd.exe`, áp dụng cả binary path và file/config/resource arguments.

Path có khoảng trắng, dấu ngoặc, Unicode và UNC được hỗ trợ khi không chứa các ký tự bị chặn. Dùng giá trị path đã resolve, không truyền chuỗi kiểu `%KAFKA_HOME%\...`. Nếu resource/path thực sự chứa ký tự bị chặn, dừng và báo không thể biểu diễn an toàn; không tự escape, encode hoặc đổi shell để lách guard.

## Checklist Windows

1. Ghi nhận `$PSVersionTable.PSVersion`, `PSEdition` và host là native Windows.
2. Chạy preflight; yêu cầu `status: ready`, `platform: windows`, version và absolute paths trong `bin\windows` hoặc installation đã chọn.
3. Giữ exact argv array, classify trước mọi lần gọi Kafka.
4. Dùng `invoke_kafka.ps1` cho đúng array và kiểm tra `$LASTEXITCODE` ngay sau child process.
5. Với mutation, hoàn tất toàn bộ preview/confirmation/revalidation protocol trước khi gọi runner đúng một lần.

## Nguồn chính thức

- Apache Kafka Windows scripts: <https://github.com/apache/kafka/tree/trunk/bin/windows>
- Python subprocess security considerations: <https://docs.python.org/3/library/subprocess.html#security-considerations>
