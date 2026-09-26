# Hướng dẫn cải thiện, đóng gói và đánh giá hai skills

Ngày nghiên cứu: 2026-09-26. Mốc nguồn: `200286cbb7cb67587b9b4131f9cd001203e51745`.

Tài liệu dành cho người duy trì `repo-foundation` và `repo-native-refactor`. Mục tiêu là giúp người khác cài được, agent dùng đúng lúc, và người duy trì biết thay đổi nào thực sự cải thiện kết quả.

Đây là kế hoạch thực hiện có tiêu chí nghiệm thu. Ngoại trừ việc viết hướng dẫn và bộ câu hỏi đi kèm, các thay đổi, cấu hình, bản đóng gói và thí nghiệm được đề xuất bên dưới **chưa được triển khai hoặc chạy**. Không xem ví dụ kết quả là kết quả đo.

[Hướng dẫn xuất bản trước đây](PUBLISHING_GUIDE.vi.md) ghi trạng thái ở thời điểm trước khi có remote/CI. Repo hiện đã được công bố; không cần thực hiện lại bước tạo repository. Hướng dẫn này bắt đầu từ giai đoạn cải thiện sau công bố.

## 1. Bắt đầu ở đâu

Chỉ triển khai đợt A trước. Chia các đợt thành commit hoặc PR riêng để có thể đánh giá và hoàn tác từng thay đổi.

| Đợt | Việc làm | Sản phẩm cần có | Điều kiện chuyển bước |
|---|---|---|---|
| A | Sửa hướng dẫn và lỗi cài đặt/xác minh | Lệnh dùng được, báo lỗi đúng, nội dung thống nhất | Người mới làm theo được; các trường hợp thất bại không báo thành công |
| B | Đóng gói runtime và kiểm tra một host | Gói sinh từ nguồn, danh sách file, ghi nhận tích hợp | Cài được đúng bản, giữ references, không mang evaluation ngoài ý định |
| C | Thử description và cách chọn skill | Kết quả cũ/mới trên cùng các câu hỏi | Biết sửa description có cải thiện hay chỉ đổi câu chữ |
| D | Đo hiệu quả hành vi | Thí nghiệm nhỏ, dữ liệu từng lượt và nhận xét | Biết giá trị tăng thêm, chi phí và kiểu task còn thất bại |

Chưa đặt mục tiêu thêm mọi host, mọi ngôn ngữ hoặc thắng mọi đối thủ. Không dùng số lượng quy tắc, test hay file làm tiêu chí chất lượng độc lập.

### Những gì đã biết tại mốc nguồn

- [CI của commit này](https://github.com/Natchannnn/repository-engineering-skills/actions/runs/36217645067) đã thành công trong lần đối chiếu trước hướng dẫn này.
- Lần kiểm tra trước đã chạy lại 31 chương trình xác minh archive và đạt 31/31. Đây là kiểm tra toàn vẹn dữ liệu, không phải 31 task mà skill thắng.
- Đã tái hiện trong thư mục tạm: lỗi mở rộng biến của lệnh archive trong README; thông báo cài thành công khi nguồn không tồn tại; file reference cũ còn lại sau khi chép đè.
- Chưa có kết quả từ bộ routing mới, gói runtime mới hay benchmark đề xuất ở đây.

## 2. Đợt A — Sửa những điều người dùng có thể gặp ngay

### A1. Dùng một cách xác minh archive thống nhất

Các nơi cần đồng bộ: [README](../README.md), [CONTRIBUTING](../CONTRIBUTING.md), [evaluation](evaluation.md) và [workflow](../.github/workflows/verify.yml).

Lệnh `pwsh -Command "... $_ ... $LASTEXITCODE ..."` trong PowerShell có hai lượt diễn giải. Chuỗi nháy kép bị mở rộng biến ở shell ngoài trước khi shell trong nhận được lệnh. Quy tắc này được mô tả trong [Microsoft: quoting rules](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules?view=powershell-7.5).

Đề xuất đưa logic vào `scripts/verify-archive.ps1`, rồi các tài liệu và CI cùng gọi script. File này chưa tồn tại; mẫu dưới đây dành cho lúc triển khai:

```powershell
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$archiveRoot = Join-Path $repoRoot 'evals-suite'
$verifiers = @(Get-ChildItem -LiteralPath $archiveRoot -Recurse -Filter verify_hashes.py -File | Sort-Object FullName)

if ($verifiers.Count -ne 31) {
    throw "Expected 31 archive verifiers; found $($verifiers.Count)."
}

Get-Command python -ErrorAction Stop | Out-Null
foreach ($verifier in $verifiers) {
    & python -B $verifier.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Archive verification failed: $($verifier.FullName)"
    }
}
Write-Output "Verified $($verifiers.Count)/31 archive packets."
```

Sau khi tạo script, tài liệu có thể dùng `pwsh -NoProfile -File ./scripts/verify-archive.ps1`, ghi rõ cần PowerShell 7 và Python. Không chép một lệnh gọi file chưa tồn tại vào README chính.

Điều kiện nghiệm thu:

| Trường hợp | Kết quả phải có |
|---|---|
| Repo nguyên vẹn | Đủ 31 script, tất cả đạt, exit 0 |
| Thiếu một verifier trong bản sao tạm | Exit khác 0; nêu số lượng thực tế |
| Sửa một byte trong payload của bản sao tạm | Exit khác 0; xác định packet lỗi |
| Chạy từ thư mục khác bằng đường dẫn script | Vẫn kiểm tra đúng repo chứa script |

Chỉ thử phá dữ liệu trên bản sao tạm. Không sửa archive gốc. Số 31 là inventory hiện tại; khi chủ đích bổ sung evidence, cập nhật inventory cùng thay đổi đó.

### A2. Cài mới phải báo lỗi đúng và bảo vệ bản đã có

[README](../README.md) đang chép đè; [installation](installation.md) đang bỏ qua thư mục đã tồn tại. Hai cách cần thống nhất.

Hợp đồng đề xuất cho lần cài mới:

1. Nhận đường dẫn repo nguồn và project đích; kiểm tra cả hai tồn tại.
2. Kiểm tra trước nguồn của **cả hai skill**: `SKILL.md`, `references/` và các file được khai báo trong gói runtime.
3. Kiểm tra trước tất cả đích. Nếu bất kỳ skill đích đã tồn tại, dừng toàn bộ trước khi sửa gì và hướng dẫn chuyển sang quy trình cập nhật.
4. Chuẩn bị các file ở vùng tạm do trình cài sở hữu; đối chiếu danh sách và nội dung với nguồn.
5. Đưa vào đích, kiểm tra lại rồi mới báo thành công. Khi một bước thất bại, báo lỗi khác 0 và trạng thái từng skill. Nếu yêu cầu cài cả bộ theo kiểu tất-cả-hoặc-không, phải có thử nghiệm rollback tương ứng.

PowerShell cần xử lý lỗi không kết thúc luồng bằng `-ErrorAction Stop` hoặc thiết lập phù hợp trong script. Với chương trình ngoài như Python, vẫn kiểm tra exit code riêng; không giả định cấu hình lỗi của PowerShell bao phủ mọi native command. [Microsoft: preference variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_preference_variables?view=powershell-7.5).

Không báo hoàn tất chỉ vì đã tạo được thư mục. Kiểm tra byte/hash ở đây nhằm phát hiện copy thiếu hoặc sai; không chứng minh nội dung skill đáng tin hay có tác giả xác thực.

Các ca cần thử trong project tạm:

| Ca | Kết quả mong đợi |
|---|---|
| Nguồn và đích hợp lệ | Hai skill có đủ file; nội dung khớp nguồn |
| Sai đường dẫn nguồn | Không tạo bản cài; exit khác 0 |
| Thiếu reference của skill thứ hai | Không để skill thứ nhất được cài trước rồi mới phát hiện lỗi đầu vào |
| Đích có một hoặc cả hai skill | Không ghi đè, không xóa; hướng dẫn cập nhật |
| Lỗi ghi khi copy | Không báo Installed; mô tả phần nào đã được tạo và khả năng phục hồi |
| Đường dẫn có dấu cách và Unicode | Cài được bằng xử lý đường dẫn literal |

Không tạo môi trường riêng cho mọi kiểu lỗi tưởng tượng. Các ca trên bảo vệ những hành vi người dùng sẽ gặp và những lỗi đã tái hiện.

### A3. Cập nhật không được trộn nội dung hai phiên bản

Chép đè giữ lại file đã bị loại khỏi bản mới. Xóa bản cũ trước khi kiểm tra bản mới lại khiến người dùng mất bản đang hoạt động khi nguồn bị lỗi.

Quy trình đề xuất: chuẩn bị bản mới hoàn chỉnh → kiểm tra → xác nhận đích là bản do quy trình này quản lý → giữ bản cũ ở vị trí backup → thay thế → kiểm tra → ghi nhận hoàn tất. Khi thay thế thất bại, khôi phục nếu có thể; nếu không, báo chính xác nơi bản cũ còn được giữ. Không xóa dữ liệu lạ hoặc symlink/reparse point không được hỗ trợ.

Nếu chưa muốn viết updater, hướng dẫn cập nhật thủ công có backup là đủ cho bản đầu. Không quảng bá cơ chế cập nhật tự động hoặc atomic khi chưa triển khai và kiểm tra.

Nghiệm thu tối thiểu: file chỉ có ở bản cũ biến mất khỏi **bản cài mới**; file chỉ có ở bản mới xuất hiện; nội dung bản cũ vẫn phục hồi được nếu bước thay thế lỗi. Trình cài chỉ quản lý hai thư mục skill được chỉ định, không dọn cả `.agents/skills` của người dùng.

### A4. Biên tập những câu hứa quá phạm vi

| Nội dung hiện tại | Điều cần sửa |
|---|---|
| `regression-free refactoring` | Mô tả refactor có phạm vi, mục tiêu giữ hành vi và kiểm tra phần bị ảnh hưởng |
| `Supported Hosts: Any...` | Tách host đã thử, đường dẫn có tài liệu, và host chưa thử |
| `Most AI benchmarks suffer...` | Bỏ nhận định tổng quát không cần thiết; mô tả thẳng dữ liệu của repo |
| `complete, unvarnished trajectory` | Nêu chính xác artifacts nào được lưu và bản ghi nào còn thiếu |
| `How to Reproduce All Results` | Đổi thành phần xác minh artifacts đã lưu; hướng dẫn chạy lại behavioral experiment ở phần riêng |
| 32 test lịch sử và 33 test hiện tại | Gắn commit/thời điểm; không sửa số lịch sử như thể lần chạy cũ có thêm test |

Mẫu giới thiệu để cân nhắc, chưa thay README hiện tại:

> Two skills for building and maintaining repositories with AI coding agents. `repo-foundation` guides implementation and contract changes. `repo-native-refactor` reviews and cleans up scoped changes while preserving the behavior the task requires. Both call for repository evidence and verification proportionate to the change.

Giữ ví dụ cụ thể về lỗi cần tránh. Không cần thay toàn bộ README bằng slogan. Đừng dùng “productionization” nếu chưa có quy trình triển khai, vận hành và kiểm tra tương ứng.

## 3. Đợt B — Đóng gói runtime và kiểm tra host

### B1. Phân biệt ba lớp

| Lớp | Câu hỏi |
|---|---|
| Định dạng | Frontmatter hợp lệ? File reference có tồn tại? |
| Tích hợp | Host thấy đúng bản và đọc đúng instructions? |
| Hành vi | Agent thực hiện công việc tốt hơn trong điều kiện đã thử? |

Theo [Agent Skills specification](https://agentskills.io/specification), `name` và `description` là metadata bắt buộc; description mô tả khả năng và thời điểm dùng. Định dạng hợp lệ chưa xác nhận hai lớp còn lại. Python dùng cho harness không tự trở thành yêu cầu runtime của skill Markdown.

### B2. Sinh gói từ một nguồn duy nhất

Giữ hai thư mục skill hiện tại làm nguồn. Tạo artifact phát hành từ commit cụ thể; không duy trì một bản nội dung thứ hai bằng cách chép tay.

Cấu trúc gói đề xuất:

```text
repository-engineering-skills-runtime/
  LICENSE
  manifest.json
  skills/
    repo-foundation/
      SKILL.md
      agents/openai.yaml
      references/...
    repo-native-refactor/
      SKILL.md
      references/...
```

Giữ `agents/openai.yaml` của foundation vì đó là metadata hiện có, không tự đổi chính sách invocation. Đây là danh sách cho phiên bản hiện tại; nếu tương lai skill cần scripts/assets, bổ sung đúng tài nguyên được tham chiếu. Không bỏ file cần thiết chỉ vì nó không phải Markdown.

Nếu một kênh cài chỉ lấy riêng thư mục skill, bảo đảm license cũng đi cùng phần được phân phối, chẳng hạn sinh một bản LICENSE trong mỗi thư mục skill của artifact. LICENSE ở root gói không đủ nếu trình cài bỏ qua root đó.

Manifest nên ghi source commit, version của gói, danh sách đường dẫn tương đối và SHA-256 của các file payload. Không đưa hash tự tham chiếu của chính manifest vào danh sách đó. SHA-256 giúp đối chiếu nội dung; không thay thế chữ ký hoặc nguồn tải đáng tin.

Generator phải:

1. Dùng danh sách đầu vào rõ ràng, giữ license.
2. Giữ byte nội dung runtime và các đường dẫn tương đối.
3. Không đưa `.git/`, cache, harness `evals/` hoặc `evals-suite/` vào gói runtime.
4. Kiểm tra mọi liên kết tài nguyên local cần dùng nằm trong gói.
5. Ghi rõ chính sách đối với checkout bẩn: từ chối hoặc ghi nhận khác biệt, không gắn commit sạch cho payload chưa commit.
6. Kiểm tra archive sau giải nén. Chưa cần cam kết ZIP byte-identical giữa mọi lần build nếu chưa cố định timestamp và metadata ZIP.

### B3. Chọn kênh phân phối sau khi kiểm tra gói

Tài liệu [Vercel Skills CLI](https://github.com/vercel-labs/skills) hỗ trợ lựa chọn skill, nguồn là đường dẫn cụ thể và liệt kê trước khi cài. Nhưng theo [installer hiện tại](https://github.com/vercel-labs/skills/blob/main/src/installer.ts), thư mục được sao chép đệ quy, không loại `evals/`. Vì vậy, trỏ vào cây nguồn hiện tại có thể cài cả harness. Đây là suy luận từ mã nguồn, chưa phải kết quả chạy installer trên repo này.

Thử trên project tạm với phiên bản CLI được ghi lại. Kiểm tra file cài thực tế, references, license, scope project/global và hành vi cập nhật. Chỉ công bố lệnh một dòng sau khi lệnh đó đã được thử từ đầu. Chọn một kênh trước: gói runtime tải về hoặc cơ chế native của host; không cần đồng thời duy trì installer riêng, npm và nhiều marketplace.

Tài liệu Codex hiện phân biệt discovery local và phân phối qua plugin; plugin là lựa chọn để phân phối bộ skill trên Codex. Chưa cần thêm MCP hay công cụ thực thi khi hai skill không cần chúng. [Codex: build skills](https://learn.chatgpt.com/docs/build-skills).

### B4. Ma trận host: tài liệu chính thức không bằng thử nghiệm của repo

| Host | Một vị trí project được tài liệu mô tả | Trạng thái của gói mới |
|---|---|---|
| Codex | `.agents/skills/<name>/SKILL.md` | Chưa thử trong kế hoạch này |
| Claude Code | `.claude/skills/<name>/SKILL.md` | Chưa thử trong kế hoạch này |
| GitHub Copilot, trên bề mặt hỗ trợ skills | `.github/skills/<name>/SKILL.md` | Chưa thử trong kế hoạch này |
| Cursor/Antigravity/host khác | Kiểm tra tài liệu và phiên bản riêng khi bổ sung | Chưa cam kết |

Nguồn cho từng dòng: [Codex](https://learn.chatgpt.com/docs/build-skills), [Claude Code](https://code.claude.com/docs/en/skills), [GitHub Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills). Đây là các lựa chọn đường dẫn, không phải danh sách đầy đủ. Không suy từ hỗ trợ một bề mặt Copilot sang mọi bề mặt Copilot.

Không gộp Codex với OpenAI Agents SDK. [Bài dùng skills để bảo trì Agents SDK](https://developers.openai.com/blog/skills-agents-sdk) mô tả Codex làm việc trên repo SDK; nó không chứng minh mọi ứng dụng SDK tự discover các thư mục này.

Nghiệm thu trên host đầu tiên:

- Cài vào project thử riêng; ghi host/version/model, OS, source commit và cách cài.
- Kiểm tra có bản cùng tên ở cấp user, project cha hoặc plugin không. Dùng profile thử hoặc cấu hình được host hỗ trợ; không xóa skills cá nhân để tạo baseline.
- Mở phiên mới, gọi rõ một skill và quan sát tool trace/path được đọc. Agent nói “đã dùng” chưa đủ. Nếu host không lộ trace, ghi giới hạn quan sát.
- Thử một tác vụ foundation, một review-only và một cleanup có phạm vi; xác minh sản phẩm, quyền sửa và phần người dùng cần giữ.
- Ghi trạng thái “đã thử” chỉ cho tổ hợp đã kiểm tra. Ghi “chưa thử” cho những tổ hợp còn lại.

## 4. Đợt C — Kiểm tra khả năng chọn đúng skill

### C1. Viết description theo mục tiêu, không theo danh sách buzzword

Hai ứng viên dưới đây chỉ để A/B với bản cũ. Giữ các metadata khác. Chưa dùng chúng để thay file hiện hành:

Foundation:

```yaml
description: Build, extend, fix, or resume work in a software repository. Use for project setup, feature implementation, bug fixes, and requirement-driven changes to contracts or architecture. For review-only requests or behavior-preserving cleanup of an existing diff, use repo-native-refactor when available.
```

Refactor:

```yaml
description: Review diffs and perform scoped, behavior-preserving cleanup using repository evidence. Use for code review, simplifying changes, fixing review findings, or explicitly requested repository rehabilitation. Respect review-only requests and preserve intentional behavior changes already authorized by the task.
```

Không ép Foundation mất khả năng thay đổi kiến trúc chỉ để tránh từ “refactor”. Hai skill có thể cùng phù hợp ở hai giai đoạn của một yêu cầu. Description không thay thế quyền và phạm vi mà người dùng đã giao.

### C2. Bộ câu hỏi đi kèm và cách dùng

[routing-cases.v1.json](evaluation-plans/routing-cases.v1.json) có 24 câu: 8 foundation, 8 refactor, 4 không cần hai skill, 4 công việc kết hợp. Có tiếng Việt và tiếng Anh.

Đây là **bộ phát triển công khai**, chưa chạy và không phải holdout. Các nhãn là kỳ vọng để kiểm tra, không phải sự thật bất biến. Rà nhãn và chuẩn bị ngữ cảnh trước; khi nhãn còn mơ hồ, sửa case trước khi chấm.

Tài liệu [tối ưu description](https://agentskills.io/skill-creation/optimizing-descriptions) đề nghị dùng câu hỏi thực tế, gồm cả trường hợp gần giống nhưng không nên kích hoạt. Với repo này, ta quan sát đường dẫn skill thực sự được đọc và tách lựa chọn ban đầu khỏi companion ở checkpoint sau.

Quy trình:

1. Đóng băng description cũ và ứng viên; các phần còn lại giống nhau.
2. Chuẩn bị context/fixture tối thiểu như `context_required` trong từng case. File câu hỏi không tự tạo fixture và không trực tiếp chạy được qua harness hiện có.
3. Mỗi lượt dùng phiên mới, cùng danh mục skill và cấu hình. Đừng cho runner đọc file JSON có nhãn; chỉ chuyển `prompt` cùng context phù hợp.
4. Không nhắc tên skill trong phép đo tự kích hoạt. Thử gọi tên trực tiếp là phép thử tích hợp riêng.
5. Quan sát lần đọc skill đầu tiên và các skill đọc sau; lưu trace. Nếu host không cho biết việc load, ghi `unobservable`, không tự coi là pass.
6. Chạy một lượt/case/description trước: 24 × 2 = 48 lượt routing. Đây là kiểm tra lựa chọn ban đầu; có thể dừng tại quyết định đầu, không ghi là đã kiểm chứng chuỗi làm việc đầy đủ.
7. Nếu cần lặp, lặp cả bộ theo kế hoạch: 24 × 2 × 3 = 144 lượt. Không chỉ chạy lại các case ứng viên bị trượt cho đến khi đạt.

Với 4 case kết hợp, chỉ đánh giá skill đầu ở phép thử routing ngắn. Kiểm tra việc dùng companion sau implementation đòi chạy đến checkpoint thật, có ngân sách và kết quả riêng.

Ghi kết quả theo nhóm và ngôn ngữ: chọn đúng lúc đầu, không kích hoạt khi nên dùng, kích hoạt không cần thiết, không quan sát được. Không cộng `unobservable` vào mẫu số như một lượt pass; công bố cả số quan sát được lẫn tổng số lượt.

Điểm routing đo chính sách lựa chọn mong muốn của dự án. Chọn một đường khác không tự chứng minh đầu ra sai; đánh giá chất lượng và quyền sửa của đầu ra riêng.

Chấp nhận description mới khi nó sửa được lỗi lựa chọn đã thấy, không tạo lỗi quyền sửa/giữ hành vi mới trong các ca liên quan, và kết quả lặp không cho thấy thoái hóa rõ. Khi cũ/mới tương đương, ưu tiên câu ngắn và rõ hơn; không tuyên bố hiệu quả tăng.

### C3. Giữ core gọn

Trước khi thêm quy tắc, trả lời: thất bại nào đã quan sát; quy tắc hiện có thiếu gì; hành vi nào phải đổi; ca đối chứng nào có thể xấu đi; làm sao đo tác dụng?

Ví dụ: lỗi hợp nhất hai domain khác nhau cần ca “không nên hợp nhất”, bên cạnh ca “nên chia sẻ policy”. Không biến một lỗi `str`/`Path` thành cấm helper nội bộ. Không biến một refactor rủi ro thành yêu cầu chạy toàn bộ test cho mọi sửa typo.

## 5. Đợt D — Đo giá trị bổ sung trên công việc thật

### D1. Tách routing khỏi năng lực khi đã dùng skill

Routing hỏi “agent có chọn đúng không?”. Thử nghiệm đầu ra hỏi “khi có skill, kết quả có tốt hơn không?”. Để đo câu hỏi thứ hai, đảm bảo skill trong nhóm treatment thực sự được đọc; ghi nhận failure-to-load riêng. Không trộn hai loại thí nghiệm thành một tỷ lệ thành công.

Tài liệu [đánh giá đầu ra skill](https://agentskills.io/skill-creation/evaluating-skills) hướng dẫn so sánh với baseline trong context mới và ghi thời gian/token. Kế hoạch dưới đây bổ sung prompt ngắn làm đối chứng, rubric cố định cho lượt báo cáo và giới hạn ngân sách phù hợp với repo này; đó là đề xuất của người viết, không phải một chuẩn chứng nhận.

### D2. Pilot riêng cho Refactor

| Nhóm | Instructions bổ sung |
|---|---|
| A | Không thêm skill/prompt kỹ thuật của dự án này; vẫn giữ host policy và hướng dẫn repo chung |
| B | Prompt kỹ thuật ngắn bên dưới |
| C | `repo-native-refactor` tại commit đã ghi nhận |

Prompt nhóm B, chốt trước khi chạy:

> Complete the requested repository task within its scope. Inspect relevant code and callers, preserve unrelated user changes and public behavior unless the task authorizes a change, and avoid speculative cleanup. Run checks that exercise affected behavior, distinguish existing failures from regressions, and report what was changed and what remains unverified.

Không gọi A là “raw model” tuyệt đối: host vẫn có system instructions và công cụ. Không cố loại bỏ policy nền để làm baseline yếu đi.

Sáu fixture đề xuất; đây là thiết kế task, chưa phải repo thực thi đã chuẩn bị:

| ID | Tình huống | Quan sát quan trọng |
|---|---|---|
| R1 | TS: diff đã đúng, đơn giản, kiểm tra đạt | Không bịa finding hoặc sửa cho đủ việc |
| R2 | TS: cùng policy validation bị lặp, có lỗi sửa một nơi quên nơi khác | Xử lý đúng policy; tests bảo vệ cả consumer; không bắt buộc tên helper |
| R3 | TS: hai đoạn giống nhau nhưng vòng đời/nghiệp vụ khác | Giữ ranh giới, không gộp vì hình thức |
| R4 | Python: legacy parser có output lỗi và thứ tự dữ liệu đang được consumer dùng, tests yếu | Bảo vệ hành vi quan sát được trước thay đổi |
| R5 | Python: diff đã chuyển sang hợp đồng v2 được task cho phép; cần review/cleanup | Không phục hồi v1 chỉ vì đó là baseline |
| R6 | TS: workspace có thay đổi người dùng và lỗi test không liên quan đã biết | Giữ user edits, phân loại lỗi đúng, hoàn thành phần được giao |

Giữ các ca ledger đã dùng để sửa skill làm regression suite, không quảng bá lại chúng như bài kiểm tra hoàn toàn mới. R4/R5 cần fixture mới, không chỉ đổi tên file trong CP2/CP3.

Thứ tự chạy:

1. Một case × ba nhóm để kiểm tra runner và cách lưu artifacts: **3 lượt hiệu chuẩn**, không tính vào kết quả chính.
2. Chốt fixture, prompt, rubric, time/token limit và chính sách retry sau hiệu chuẩn.
3. Sáu case × ba nhóm × ba lần = **54 lượt chính**. Tổng kế hoạch gồm hiệu chuẩn: **57 lượt**.
4. Xáo trộn hoặc cân bằng thứ tự nhóm trong từng case/lần lặp; ghi lịch chạy.
5. Chỉ mở rộng sau khi xem kết quả và chi phí. Ba lần lặp chưa đủ cho tuyên bố thống kê rộng.

Nếu chưa đủ ngân sách, chạy 18 lượt (mỗi tổ hợp một lần) và gọi đúng tên là khảo sát ban đầu. Không cam kết trước một ngân sách tiền vì chưa biết model, giá và độ dài task. Ước lượng từ hiệu chuẩn rồi đặt trần lượt, thời gian và chi phí.

### D3. Foundation cần một bộ câu hỏi khác

Không lấy điểm Refactor để kết luận Foundation hiệu quả. Pilot Foundation riêng nên gồm: dựng một vertical slice dùng được; thêm tính năng vào repo có conventions; sửa bug với regression test; migration được yêu cầu; tiếp tục từ notes sai; bảo toàn workspace có user edits.

Cùng cách bố trí A/B/C, nhưng C là Foundation. Muốn đo Foundation đơn lẻ, không cài companion trong tất cả các nhóm của thử nghiệm đó và ghi rõ cấu hình. Nếu muốn đo cả bộ, thêm nhóm riêng; không đổi giữa chừng.

### D4. Chấm kết quả có thể bảo vệ được

Chốt điều kiện đúng của fixture trước lượt báo cáo. Hiệu chuẩn được dùng để sửa rubric; sau đó khóa rubric. Nếu phát hiện rubric sai, sửa có version và chấm lại mọi nhóm bị ảnh hưởng.

| Chỉ số | Cách ghi |
|---|---|
| Hoàn thành task | Các yêu cầu chấp nhận độc lập đã đạt/chưa đạt |
| Vi phạm nghiêm trọng | Sửa khi chỉ được review, làm mất user edits, phá hợp đồng không được phép, làm yếu test |
| Regression | Hành vi trước đúng, sau sai; tách khỏi thay đổi được yêu cầu |
| Finding sai | Finding bị kiểm tra thực tế bác bỏ; lưu lý do, không dựa vào bất đồng phong cách |
| Thay đổi ngoài phạm vi | Số file/hunk kèm đánh giá quan hệ với task |
| Churn | Số file và dòng sửa; không tự cho điểm cao khi ít dòng nhưng task chưa xong |
| Chi phí | Input/output/cache/reasoning tokens nếu host cung cấp, thời gian và chi phí theo giá tại ngày chạy |
| Công review | Thời gian người review trên task chuẩn hóa; nếu chưa có người đo thì để chưa đo |

Các pass/fail về contract phải dùng kết quả quan sát được. Đánh giá maintainability có yếu tố phán đoán nên lưu lập luận, không giả làm phép đo khách quan hoàn toàn. Không chấm điểm vì chọn `count` thay `migrated`, predicate dương thay âm, hoặc ít file hơn nếu chưa có hậu quả bảo trì cụ thể.

Vi phạm nghiêm trọng không được bù bằng điểm prose cao. Báo riêng số task đạt và số vi phạm; đừng chỉ báo một điểm tổng.

### D5. Giữ điều kiện công bằng

- Cùng model version, host version, tools, quyền, fixture, hướng dẫn repo và ngân sách task. Ghi những setting không điều khiển được.
- Context và workspace mới mỗi lượt; không cho kết quả nhóm trước vào nhóm sau. Kiểm tra baseline không vô tình nạp skill cấp user hoặc project cha.
- Runner không thấy rubric riêng, expected patch hay đáp án. Hidden checks chạy từ grader đáng tin, không phải chỉ từ tests mà runner có thể sửa.
- Thư mục làm việc riêng chỉ tách trạng thái; nó không tự tạo ranh giới bảo mật. Đặt dữ liệu grader ngoài phạm vi truy cập của runner khi host hỗ trợ. Nếu chỉ không đưa chúng vào prompt nhưng runner vẫn có thể đọc trên cùng filesystem, ghi đúng giới hạn đó.
- Judge nhận yêu cầu và artifacts cần chấm, được ẩn nhãn nhóm. Giữ khóa đối chiếu riêng đến sau chấm. Code style vẫn có thể lộ dấu hiệu; mô tả giới hạn blinding.
- Ghi việc ai thiết kế task, ai sửa skill, ai chấm. Một agent khác chưa tự động tạo ra “đánh giá độc lập”.
- Chốt retry cho lỗi hạ tầng. Lưu lượt lỗi, lý do và lượt thay thế. Timeout do dùng hết ngân sách vẫn là kết quả, không xóa khỏi báo cáo.
- Khóa một tập holdout mới trước khi đánh giá cuối. Tập đã xem để sửa skill trở thành development set; 24 câu công khai kèm hướng dẫn này không phải holdout.
- Lặp nhiều lần trên cùng sáu task không tạo ra 54 loại task độc lập. Báo theo từng task và từng lượt, không suy rộng bằng một tỷ lệ chung.

### D6. Khi nào thêm đối thủ

Sau khi pipeline ổn, chọn một skill phù hợp với task, chẳng hạn [tidy](https://github.com/mblode/agent-skills/blob/main/skills/tidy/SKILL.md) hoặc [clean-code](https://github.com/cskwork/clean-code). Ghi commit và cài đúng dependencies/references của họ. Dùng task và rubric đã khóa; không sửa để ưu tiên quy tắc riêng của mình.

Thêm một nhóm vào pilot 6 × 3 lần cần **18 lượt chính bổ sung**, nâng từ 54 lên 72. Chạy cân bằng về thời gian/model; nếu model/host thay đổi đáng kể, không ghép số cũ và mới thành so sánh có kiểm soát.

Muốn đo “Superpowers + skills của mình”, cần nhóm Superpowers đơn lẻ. So với baseline trống không tách được đóng góp riêng của bộ skills. Không ép mọi đối thủ vào workflow khác với cách họ được thiết kế rồi kết luận họ yếu.

## 6. Lưu evidence vừa đủ để người khác kiểm tra

Lưu thử nghiệm mới ở vùng riêng, không chép vào archive đã niêm phong. Vị trí chạy có thể nằm ngoài repo; chỉ đưa artifacts được chọn vào Git sau khi rà nội dung và kích thước.

```text
experiment-<id>/
  protocol.md             Cấu hình, rubric, lịch chạy, ngân sách, retry policy
  fixtures/               Trạng thái đầu hoặc ref/hash để khôi phục
  skill-snapshots/         Các phiên bản instructions đã dùng
  runner-inputs/           Prompt và ngữ cảnh runner được phép xem
  grader-private/          Checks, expected outcomes, khóa nhãn; không mount cho runner
  runs/<run-id>/
    run.json
    trace.jsonl
    candidate.patch
    artifacts/            File mới/untracked/binary cần để tái dựng
    verification.txt
    judgment.json
  summary.md
```

Một patch Git thông thường không chứa mọi untracked file. Kiểm tra khả năng dựng lại candidate bằng baseline + patch + artifacts, hoặc dùng snapshot bytes đã xác minh. Hash toàn cây không tự tái tạo được file đã thất lạc.

Mẫu record dưới đây không thuộc schema harness hiện có. Đây là đặc tả nháp để thống nhất dữ liệu trước khi viết adapter; `null` là chưa đo, không phải 0 hay pass:

```json
{
  "record_version": "proposal-1",
  "run_id": "R1-C-01",
  "phase": "main",
  "case_id": "R1",
  "arm": "C",
  "replicate": 1,
  "model": null,
  "host_version": null,
  "skill_commit": null,
  "fixture_hash": null,
  "protocol_hash": null,
  "skill_load_observed": null,
  "task_success": null,
  "critical_violation_count": null,
  "tokens": {"input": null, "output": null},
  "duration_seconds": null,
  "cost_usd": null,
  "status": "not_run"
}
```

Bản ghi thật phải đủ danh tính phiên bản, baseline và cấu hình để diễn giải. Không gọi `harness.py score` với mẫu trên: scoring schema cũ và format nghiên cứu mới là hai thứ khác nhau.

## 7. Tổ chức thay đổi và giới hạn công việc

Commit/PR đề xuất:

1. `fix: make documented installation and verification fail clearly` — sửa scripts/tài liệu, kiểm tra lỗi đã biết.
2. `build: package runtime skills from a recorded source revision` — generator, manifest, kiểm tra gói và host đầu tiên.
3. `eval: compare skill routing descriptions` — bộ câu hỏi, runner/trace, kết quả cũ/mới; chỉ sửa description nếu có lý do.
4. `eval: add a scoped behavioral pilot` — fixture, protocol và kết quả. Tách việc xây runner khỏi báo cáo kết quả nếu cần.

Tên là ví dụ; không tạo PR rỗng. Nếu tạo branch, có thể dùng `codex/install-reliability`, `codex/runtime-package`, `codex/routing-eval`, `codex/behavioral-pilot`.

Khi sửa runtime instructions, giữ bản trước để so sánh và ghi changelog của gói. Phân biệt version bundle, version từng skill và commit; không ép tất cả trùng nhau hoặc sửa version trong archive lịch sử.

Mỗi đợt có điểm dừng: acceptance đã đạt, không có lỗi mới liên quan và chưa có bằng chứng đòi mở rộng thì hoàn tất đợt. Không yêu cầu AI “tìm thêm cho đến hoàn hảo” sau mỗi lần pass.

## 8. Prompt có thể giao cho agent ở lượt tiếp theo

### Thực hiện đợt A

> Đọc docs/IMPROVEMENT_GUIDE.vi.md và thực hiện riêng đợt A. Đồng bộ README, CONTRIBUTING và docs liên quan; sửa lỗi cài đặt và xác minh đã nêu, ưu tiên một nguồn logic dùng chung. Viết và chạy các kiểm tra acceptance cần thiết trong thư mục tạm. Giữ nguyên nội dung hai SKILL.md và archive evals-suite. Báo file đã đổi, kết quả kiểm tra, phần chưa xác minh. Không commit, push hoặc publish trong lượt này.

### Chuẩn bị đợt B

> Thực hiện đợt B từ docs/IMPROVEMENT_GUIDE.vi.md: sinh gói runtime từ nguồn hiện tại có ghi nhận revision, giữ license và metadata cần thiết, kiểm tra inventory/hash/references sau giải nén. Thử cài file vào project tạm. Tách kết quả copy file khỏi xác nhận host đọc skill; ghi phần cần thao tác trên host nếu chưa kiểm chứng được. Chưa công bố artifact hoặc cài global.

### Chuẩn bị thí nghiệm, chưa chạy model

> Dùng đợt C/D trong docs/IMPROVEMENT_GUIDE.vi.md để chuẩn bị fixture, protocol, rubric và cách lưu kết quả. Tái sử dụng harness khi phù hợp, nhưng không giả định JSON nghiên cứu đã tương thích với schema cũ. Kiểm tra runner bằng dữ liệu giả được gắn nhãn. Chưa chạy campaign có model; báo cấu hình và ước lượng ngân sách để chọn phạm vi cụ thể.

## 9. Cách đọc nguồn và đánh giá tiến bộ

Nguồn host/CLI phía trên được đọc tại ngày nghiên cứu; đường dẫn và hành vi có thể thay đổi. Khi công bố hỗ trợ, ghi version đã thử. Các bảng acceptance, số lượt pilot và quy trình release trong hướng dẫn này là đề xuất cho repo, không phải kết quả chứng nhận từ các nguồn đó.

Một thay đổi đáng giữ khi nó sửa được vấn đề có bằng chứng, không làm hỏng trường hợp đối chứng liên quan và có chi phí hợp lý. Nếu không thấy cải thiện, giữ kết quả đó trong báo cáo và cân nhắc bỏ thay đổi. Người dùng tự cài và hoàn thành một task thật là bằng chứng hữu ích hơn thêm một vòng chấm điểm cảm tính.
