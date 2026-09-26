# Hướng dẫn chuẩn bị và phát hành Repository Engineering Skills

Tài liệu này hướng dẫn người duy trì chuẩn bị repo, công bố trên GitHub và cập nhật các phiên bản sau. Các lệnh bên dưới dành cho PowerShell trên Windows. Chạy từng khối, kiểm tra kết quả rồi mới chuyển bước; dừng lại nếu một lệnh báo lỗi.

Đây là hướng dẫn và các mẫu đề xuất. Việc tạo file này không tự thêm CI, cài skill, tạo repository GitHub, commit, push hay phát hành.

## 1. Điểm xuất phát và mục tiêu

Tại thời điểm viết hướng dẫn:

- Repository: `C:\Users\Natch\Desktop\SKILLS-MAIN`.
- Commit đã audit: `ae83651cf3f82c5db61c8bf3e8b5accd599f2f29`.
- Branch hiện tại: `master`; chưa có remote.
- Đã có `LICENSE` MIT, `.gitignore`, `.gitattributes`, hai skill và evaluation archive.
- Kết quả audit gần nhất: 32 test refactor, 26 test foundation; 31 chương trình kiểm tra hash đạt trong fresh clone và Git archive.
- Môi trường audit: Windows, Python 3.14.5. Các con số này là kết quả tại commit trên, không phải badge động cho mọi phiên bản sau.

Một repo dễ dùng phải trả lời được: nó làm gì, cài thế nào, dùng khi nào, kết quả nào đã được kiểm tra và báo lỗi ở đâu. Không cần logo, website hoặc nhiều badge để đạt mục tiêu này.

## 2. Tên và cấu trúc repository

Tên GitHub đề xuất: `repository-engineering-skills`. Tên này không bắt buộc; tên thư mục local vẫn có thể là `SKILLS-MAIN`.

Giữ tên hai skill để người dùng không phải đổi cách gọi. Không di chuyển archive hoặc đổi cấu trúc harness chỉ để làm cây thư mục đẹp hơn.

Cấu trúc tài liệu đề xuất:

```text
README.md                       Giới thiệu, cài nhanh, ví dụ, giới hạn
LICENSE                         Giữ giấy phép MIT hiện có
CHANGELOG.md                    Thay đổi theo từng bản phát hành
CONTRIBUTING.md                 Cách báo lỗi, sửa đổi và chạy kiểm tra
BENCHMARK_REPORT.md             Kết quả lịch sử và giới hạn thí nghiệm
docs/
  installation.md              Cài đặt, cập nhật, gỡ cài đặt
  usage.md                     Ví dụ và cách chọn skill
  evaluation.md                Cách chạy harness và xác minh archive
  PUBLISHING_GUIDE.vi.md        Hướng dẫn người duy trì này
.github/
  workflows/verify.yml          Kiểm tra tự động
repo-foundation/
repo-native-refactor/
evals-suite/
```

Chỉ tạo các tài liệu khi có nội dung thực. Có thể giữ hướng dẫn cài/dùng ngay trong README trước, rồi tách ra khi dài. Issue template và pull-request template có thể bổ sung sau.

## 3. Biên tập README cho người mới

README chính nên dùng tiếng Anh nếu muốn người dùng quốc tế tham gia. Hướng dẫn tiếng Việt có thể đặt riêng để tránh phải cập nhật hai bản giống nhau ở mọi lần sửa.

Thứ tự nội dung nên là:

1. Mô tả ngắn và đối tượng sử dụng.
2. Bảng chọn giữa hai skill.
3. Cài đặt cho môi trường đã thử.
4. Ba ví dụ sử dụng.
5. Giới hạn và trạng thái tương thích.
6. Liên kết evaluation, đóng góp và giấy phép.

Mẫu mở đầu có thể dùng:

```markdown
# Repository Engineering Skills

Two skills for AI coding agents working in software repositories.

- **repo-foundation** guides project setup, feature development, contract changes, and work across sessions.
- **repo-native-refactor** reviews and refines changes while preserving intended behavior and repository conventions.

Both emphasize bounded changes, proportionate verification, and explicit handling of uncertainty.

The repository includes evaluation harnesses and archived comparison runs. These results cover a small set of repository tasks; they do not establish consistent improvements across all models, languages, or projects.
```

Bảng lựa chọn nên giải thích foundation dùng cho xây dựng/thay đổi tính năng; refactor dùng cho review hoặc cleanup có phạm vi. Người dùng có thể dùng từng skill riêng. Sửa typo không cần gọi cả hai.

### Cách viết tránh phóng đại

| Cách viết nên thay | Cách viết cụ thể hơn |
|---|---|
| Architectural lifecycle engine | Workflow for starting and extending repositories |
| Prevents models from breaking contracts | Instructs agents to preserve public contracts |
| Enforces DRY consolidation | Guides consolidation when shared ownership and maintenance benefits justify it |
| Production-hardened | Tested on Windows with Python 3.14.5 — nếu đúng với bản được nói đến |
| The Brutal Truth | Observed failures |
| Full Marks / Winner | Điểm, điều kiện chạy và giới hạn |

Không cần tự nhận là chuyên gia. Nếu muốn nói về AI hỗ trợ, chỉ mô tả cách đã dùng và trách nhiệm duy trì; không gọi audit bằng LLM là chứng nhận của tổ chức độc lập.

Tách rõ ba loại số liệu: test của harness; kiểm tra tính toàn vẹn archive; thí nghiệm hành vi agent. Không đặt cùng một kết quả unit test ở hai cột control/treatment như thể đó là ablation.

Các câu trích dẫn skill cũ trong benchmark phải được ghi là phiên bản lịch sử; hướng dẫn sử dụng hiện tại phải theo `SKILL.md` hiện tại.

## 4. Viết và thử hướng dẫn cài đặt

Đối với hai skill hiện tại, phần cần để agent sử dụng là `SKILL.md` và thư mục `references/`. Harness và archive phục vụ đánh giá, không cần nạp như chỉ dẫn runtime.

Để tránh trình cài tự tìm cả những bản `SKILL.md` đóng băng trong archive, hướng dẫn cài phải chỉ rõ hai thư mục skill hiện tại. Không mặc định dùng một lệnh quét toàn bộ repo khi chưa thử cơ chế discovery đó.

### Cài vào một project Codex trên Windows

Codex hỗ trợ skill ở `.agents/skills/` trong project. Xem [tài liệu OpenAI về skill trong repository](https://developers.openai.com/fr-FR/blog/skills-agents-sdk).

Mẫu dưới đây cài từ checkout local vào một project do bạn chọn. Thay `C:\Projects\my-project` bằng project thật; thư mục đó phải tồn tại. Đoạn này chưa được thực thi vào project của bạn.

```powershell
$skillSource = 'C:\Users\Natch\Desktop\SKILLS-MAIN'
$targetProject = 'C:\Projects\my-project'

if (-not (Test-Path -LiteralPath $targetProject -PathType Container)) {
    throw 'Hãy chọn đường dẫn project có thật.'
}

$skillInstallRoot = Join-Path $targetProject '.agents\skills'
$skillNames = @('repo-foundation', 'repo-native-refactor')

foreach ($skillName in $skillNames) {
    $destination = Join-Path $skillInstallRoot $skillName
    if (Test-Path -LiteralPath $destination) {
        throw "Skill đã tồn tại: $destination. Hãy kiểm tra bản đang cài trước khi cập nhật."
    }
    $source = Join-Path $skillSource $skillName
    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
        throw "Không tìm thấy skill: $source"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $source 'references') -PathType Container)) {
        throw "Không tìm thấy references: $source"
    }
}

foreach ($skillName in $skillNames) {
    $source = Join-Path $skillSource $skillName
    $destination = Join-Path $skillInstallRoot $skillName
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $source 'SKILL.md') -Destination $destination
    Copy-Item -LiteralPath (Join-Path $source 'references') -Destination $destination -Recurse
}
```

Khi viết hướng dẫn công khai, đổi đường dẫn source thành đường dẫn checkout của người dùng. Nếu tên repo GitHub khác tên thư mục local, ghi rõ chỗ này.

Mở một phiên mới trong project đích và yêu cầu agent dùng đúng skill. Xác nhận nó đọc bản vừa cài, không phải bản khác đã có ở cấp user. Thử trên project nhỏ trước khi ghi trạng thái tích hợp là “tested”. Việc copy file đúng chưa chứng minh discovery của mọi phiên bản host đều hoạt động.

Ba prompt mẫu cho `docs/usage.md`:

```text
Use repo-foundation to add JSON export to this CLI. Preserve the existing commands and error behavior. Verify the new output and document the command.
```

```text
Use repo-native-refactor to review the current diff. Report actionable findings with file references. Review only; do not edit source files.
```

```text
Use repo-native-refactor to clean up the current diff where a concrete maintenance or correctness problem is established. Preserve the authorized behavior and avoid unrelated changes. Run the affected checks after edits.
```

Ghi riêng các host đã thử. Không suy ra hỗ trợ đầy đủ Claude Code, Cursor hoặc OpenCode chỉ từ việc cùng đọc Markdown. Cũng không quảng bá benchmark skill cũ như phép thử tích hợp của phiên bản mới.

## 5. Thêm kiểm tra tự động trên GitHub

CI là workflow tự chạy khi push hoặc mở pull request. Bắt đầu với Windows và Python 3.14 để khớp môi trường đã audit. Chưa cần hứa hỗ trợ mọi OS hoặc Python version.

Tạo `.github/workflows/verify.yml` theo mẫu sau. Đây là cấu hình đề xuất, chưa được chạy trên GitHub. Các action version trong mẫu được đối chiếu với [setup-python chính thức](https://github.com/actions/setup-python); GitHub hướng dẫn đặt workflow trong [`.github/workflows`](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

```yaml
name: Verify

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  windows:
    runs-on: windows-latest
    timeout-minutes: 15

    steps:
      - name: Exercise Windows line-ending conversion
        run: git config --global core.autocrlf true

      - uses: actions/checkout@v7

      - uses: actions/setup-python@v7
        with:
          python-version: '3.14'

      - name: Refactor harness tests
        run: python -B -m unittest discover -s repo-native-refactor/evals/tests -v

      - name: Foundation harness tests
        run: python -B -m unittest discover -s repo-foundation/evals/tests -v

      - name: Validate foundation assets
        run: python -B repo-foundation/evals/harness.py validate

      - name: Verify archived evidence
        shell: pwsh
        run: |
          $verifiers = @(Get-ChildItem -LiteralPath evals-suite -Recurse -Filter verify_hashes.py -File)
          if ($verifiers.Count -ne 31) {
            throw "Expected 31 archive verifiers; found $($verifiers.Count). Review the inventory."
          }
          foreach ($verifier in $verifiers) {
            python -B $verifier.FullName
            if ($LASTEXITCODE -ne 0) {
              throw "Archive verification failed: $($verifier.FullName)"
            }
          }

      - name: CP2 treatment
        run: python -B repo-foundation/evals/harness.py verify CP2_SLICE evals-suite/ablation_cp2/treatment/workspace

      - name: CP3 treatment
        run: python -B repo-foundation/evals/harness.py verify CP3_EVOLUTION evals-suite/ablation_cp3_hardcore/treatment/workspace

      - name: CP4 continuity
        run: python -B repo-foundation/evals/harness.py verify CP4_CONTINUITY evals-suite/gate3_space_bunny/gate3-manual-v2-A-rep01
```

Nếu bạn giữ tên branch `master`, đổi phần trigger `main` tương ứng. Nếu số packet thay đổi có chủ đích, cập nhật inventory trong CI cùng thay đổi đó. Không bỏ kiểm tra số lượng để làm CI xanh.

Workflow này kiểm tra deterministic behavior; không gọi model và không chứng minh hiệu quả của skill trên task mới. Tạo thêm các thử nghiệm agent riêng khi muốn mở rộng claim.

## 6. Giữ archive và lịch sử Git rõ ràng

Không sửa file trong `evals-suite` để đổi giọng văn hoặc format cho đồng nhất: đó là dữ liệu lịch sử có hash. Ghi đính chính ở tài liệu hiện tại, nêu rõ bản và phạm vi liên quan.

Giữ các ngoại lệ `.pyc` trong `.gitignore` và quy tắc `evals-suite/** -text -eol` trong `.gitattributes`. Đừng chạy formatter, chuẩn hóa newline hoặc xóa bytecode trên archive.

Một commit ban đầu lớn là chấp nhận được cho lần công bố đầu. Không cần tạo lịch sử giả hoặc tiếp tục xóa `.git` để có repo “sạch”. Từ đây, giữ lịch sử để người khác xem được thay đổi.

Commit nên diễn đạt kết quả cụ thể, ví dụ:

```text
docs: explain installation and intended use
ci: verify harnesses and archived evidence on Windows
fix: preserve invalid snapshot bundles during default export
test: cover snapshot rollback after rename failures
```

Không bắt buộc Conventional Commits; quan trọng là nhất quán và có nghĩa. Review diff trước khi commit; không sửa lịch sử đã công bố chỉ để đổi câu chữ nhỏ.

## 7. Chuẩn bị local trước khi push

### 7.1. Kiểm tra đúng repository

```powershell
Set-Location -LiteralPath 'C:\Users\Natch\Desktop\SKILLS-MAIN'
git status --short
git branch --show-current
git remote -v
```

### 7.2. Chọn tên branch

Repo hiện chỉ có `master`. Nếu chọn dùng `main` cho hướng dẫn và CI mới, đổi tên một lần:

```powershell
git branch -m main
```

`master` không sai. Đổi tên chỉ để mọi ví dụ, CI và branch mặc định thống nhất. Lệnh trên không cần force.

### 7.3. Commit phần tài liệu đã hoàn thành

Sau khi viết README và docs thực tế, chọn từng nhóm file bằng `git add`. Ví dụ này giả định bạn đã hoàn thành nội dung trong `docs/`:

```powershell
git add README.md docs/
git diff --cached --stat
git diff --cached --check
git diff --cached
git commit -m "docs: explain installation and intended use"
```

Đọc diff để chắc rằng các đường dẫn máy cá nhân và mẫu placeholder chỉ xuất hiện đúng chỗ của tài liệu hướng dẫn, không bị nhầm là lệnh cài công khai hoàn chỉnh.

Nếu đã tạo workflow:

```powershell
git add .github/workflows/verify.yml
git diff --cached
git commit -m "ci: verify harnesses and archived evidence on Windows"
```

Commit `CONTRIBUTING.md`, `CHANGELOG.md` và bản biên tập benchmark theo nhóm phù hợp sau khi chúng thực sự tồn tại. Không copy lệnh `git add` với tên file chưa được tạo.

### 7.4. Xác minh bản sắp công bố

Chạy bộ kiểm tra trong CI ở trên trên bản cuối. Nếu chỉ thay đổi tài liệu, kiểm tra link, đường dẫn và ví dụ cài/dùng là phần đặc biệt quan trọng. Trước release, tạo một fresh clone khác để làm theo README từ đầu.

Ghi trạng thái “tested on Windows with Python 3.14.5” nếu chưa kiểm tra các môi trường khác. Không lấy yêu cầu Python của riêng refactor harness để suy ra yêu cầu của toàn bộ suite.

## 8. Tạo repository GitHub và push lần đầu

Máy hiện có Git và Python; chưa thấy `gh` trên PATH. Có thể dùng trình duyệt cộng Git, không cần cài thêm GitHub CLI.

Trên GitHub, tạo repository mới với tên đã chọn. Chọn Public khi đã sẵn sàng công khai. Không khởi tạo thêm README, `.gitignore` hoặc license trên GitHub vì local đã có. Sau đó copy HTTPS URL GitHub cung cấp. Đây là quy trình trong [hướng dẫn import repo local của GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

Nếu chọn tên `repository-engineering-skills` dưới tài khoản `Natchannnn`, các lệnh là:

```powershell
git remote add origin https://github.com/Natchannnn/repository-engineering-skills.git
git remote -v
git push -u origin main
```

Chỉ chạy sau khi repository đó đã được tạo. Nếu tên/owner khác, dùng URL thật thay cho ví dụ. Khi Git yêu cầu đăng nhập, làm theo luồng xác thực của Git/Git Credential Manager; không đặt token trong URL hoặc commit.

Nếu gặp lỗi, không thêm `--force`. Kiểm tra thông báo trước: remote đã tồn tại, chưa đăng nhập, repository không đúng URL, hay GitHub đã có commit riêng là những tình huống khác nhau.

## 9. Hoàn thiện trang GitHub

Description gợi ý:

```text
Two AI coding skills for repository development and scoped refactoring, with evaluation harnesses and archived comparison runs.
```

Topics gợi ý: `agent-skills`, `coding-agents`, `code-review`, `refactoring`, `software-engineering`, `evaluation`.

Chỉ thêm badge phản ánh dữ kiện thật: giấy phép và kết quả workflow đã chạy. Chưa cần logo hoặc banner. Không dùng badge “100% reliable”, “production ready” hoặc “independently certified”.

Sau lần push đầu, vào Actions, mở workflow Verify và kiểm tra từng bước. Chỉ đánh dấu CI passed khi run trên commit tương ứng đã thành công. Có thể bổ sung quy tắc yêu cầu CI đạt trước merge sau khi workflow chạy ổn.

## 10. Tạo release đầu tiên

Đề xuất dùng `v0.1.0` cho bản công bố đầu của **gói repository thống nhất**. Đây là đề xuất version của bundle; repo hiện có version nội bộ của skill/harness, nên ghi rõ chúng riêng và không đổi các version trong archive lịch sử. Không có yêu cầu phải đổi version skill đang hoạt động chỉ để khớp ví dụ này.

Sau khi commit cuối đã push và CI đạt, tạo annotated tag:

```powershell
git status --short
git log -1 --oneline
git tag -a v0.1.0 -m "First public release of the unified skills package"
git push origin v0.1.0
```

Trên GitHub: Releases → Draft a new release → chọn tag vừa tạo → viết nội dung → Publish release. Có thể lưu Draft trước. Chỉ đánh dấu pre-release nếu bạn thực sự muốn công bố đó là bản thử nghiệm; version 0.x không tự động bắt buộc lựa chọn này. Xem [hướng dẫn release của GitHub](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

Release notes nên có:

- Những thành phần được phát hành.
- Hướng dẫn cài và ví dụ dùng.
- Commit, môi trường và kết quả kiểm tra của bản phát hành.
- Giới hạn: benchmark nhỏ, môi trường chưa thử, chưa xác minh crash/power-loss.
- Cách báo lỗi.

Nếu attach ZIP gọn chỉ chứa runtime skills, cần kèm license, giữ references, ghi rõ không chứa evaluation archive và thử cài chính ZIP đó. Đây là tiện ích bổ sung, không phải điều kiện để phát hành lần đầu.

## 11. Duy trì sau khi phát hành

Với mỗi thay đổi: mô tả vấn đề → sửa trong phạm vi → chạy kiểm tra liên quan → đọc diff → commit rõ nghĩa. Thay đổi hành vi cần regression case tương ứng. Thay đổi tài liệu cần kiểm tra ví dụ và link.

Giữ tag đã phát hành cố định; tạo tag mới cho bản sửa tiếp theo. Không thay file bằng chứng lịch sử để làm kết quả cũ trông tốt hơn.

`CONTRIBUTING.md` chỉ cần đủ ngắn để người khác bắt đầu: cách chạy kiểm tra, cách báo lỗi, điều gì không được sửa trong archive và quy tắc PR có phạm vi. Với báo lỗi skill, yêu cầu phiên bản skill, host/model, task, hành vi mong đợi và hành vi thực tế; người báo có thể rút gọn dữ liệu nhạy cảm.

`CHANGELOG.md` ghi tác động với người dùng, không sao chép mọi commit. Phân biệt thay đổi nội dung skill với thay đổi harness.

## 12. Thứ tự làm đề xuất

1. Viết lại README và hướng dẫn cài/dùng.
2. Thử cài runtime vào một project nhỏ, xác nhận discovery và hai tình huống sử dụng.
3. Biên tập benchmark cho chính xác, giữ nguyên archive.
4. Thêm CI, CONTRIBUTING và CHANGELOG ngắn.
5. Commit theo nhóm, tạo repo GitHub trống và push.
6. Chờ CI, kiểm tra README từ fresh clone, tạo tag/release.

Mục tiêu của lần phát hành đầu là người khác có thể hiểu, dùng, kiểm tra và phản hồi dự án. Những cải thiện hình thức có thể làm sau khi các bước đó hoạt động.
