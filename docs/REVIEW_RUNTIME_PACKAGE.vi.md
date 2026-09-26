# Review Đợt B: gói runtime

Ngày kiểm tra: 2026-09-27, múi giờ Asia/Saigon.

## Kết luận

Đợt A đã được commit đúng SHA `d4776c42c183cd7c4a00b5e3511db59aa7c523f2`, tác giả `Natchannnn`. Trong lượt kiểm tra này, hai file `scripts/package-runtime.ps1` và `scripts/test-package.ps1` vẫn chưa được Git theo dõi.

**BLOCK việc chốt Đợt B như một generator phát hành từ commit đã xác định.** Nhánh scratch build hoạt động, nhưng nhánh repo sạch bị lỗi và nguồn payload chưa bị giới hạn vào commit. Không mở lại kết luận về installer của Đợt A.

## Các kiểm tra thực thi

| Kiểm tra | Quan sát |
|---|---|
| Git HEAD, tác giả và danh sách file trong commit | Khớp báo cáo Đợt A |
| Acceptance suite `scripts/test-package.ps1` trên working tree thật | PASS; dùng `-AllowDirty`; ZIP 35,547 byte trong lần chạy này |
| Cài từ gói đã giải nén bằng installer trong repo | PASS; 16 file được installer xác minh |
| Generator nguyên bản trên fixture Git đã commit sạch, output ngoài repo | FAIL trước đóng gói: gọi method trên null |
| Generator nguyên bản với `-AllowDirty`, thêm file ignored giả lập | Build thành công; cả hai file ignored lọt vào ZIP |
| Đối chiếu trực tiếp ZIP với manifest bằng Python | Inventory và tất cả SHA-256 khớp |
| Fixture sạch sau khi sửa duy nhất phép chuẩn hóa output Git, chỉ trong TEMP | Build thành công nhưng file ignored vẫn lọt; manifest báo `working_tree_clean: true` |
| So sánh `generated_at` với UTC thực tế | Timestamp ghi thời gian phía trước UTC khoảng 7 giờ |
| `git diff --check` | PASS |

Gói bình thường có 17 payload files: 16 file thuộc hai skill và một LICENSE ở gốc; `manifest.json` không tự tính vào danh sách payload. Không có mâu thuẫn giữa số 17 của package và số 16 của installer.

Fixture sạch dùng nội dung runtime và script hiện tại trong một Git repository thử độc lập. Đây là phép kiểm tra generator, không phải tuyên bố đã chạy release từ một commit Đợt B có thật. Không chạy lại harness Python/31 archive packets trong lượt này.

## R1 — P1: nhánh repo sạch bị lỗi ngay khi đọc Git status

Vị trí: `scripts/package-runtime.ps1:27`.

```powershell
$dirtyStatus = (& git -C $repoRoot status --porcelain).Trim()
```

Với repo sạch, Git không in dòng nào; kết quả trong PowerShell là null. Gọi `.Trim()` trên đó ném lỗi `You cannot call a method on a null-valued expression.`. Mình đã tái hiện với generator nguyên bản trên fixture sạch.

Suite hiện luôn truyền `-AllowDirty` và đang chạy trên repo chứa các script untracked, nên chưa đi qua trạng thái sạch làm lộ lỗi này. Flag không tự sửa lỗi null; có output dirty mới giúp phép `.Trim()` ở lần thử hiện tại không lỗi.

Hướng sửa:

```powershell
$statusLines = @(& git -C $repoRoot status --porcelain)
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to inspect repository status.'
}
$isDirty = $statusLines.Count -gt 0
if ($isDirty -and -not $AllowDirty) {
    throw 'Working tree is dirty.'
}
```

Đây là mẫu cho nhánh kiểm tra status; cần cập nhật trường `working_tree_clean` tương ứng. Test bắt buộc: repo sạch build thành công không dùng `-AllowDirty`, repo dirty bị từ chối, và Git status thất bại không bị coi là sạch.

## R2 — P2: payload được lấy từ filesystem, không phải inventory của commit

Vị trí: `scripts/package-runtime.ps1:76`, `91`, `114–115`.

Generator liệt kê mọi file trong `references/` và `agents/`. Git status không liệt kê file ignored, nên hai điều kiện “status sạch” và “đường dẫn nằm dưới references” chưa đủ để chứng minh file đó thuộc commit nguồn.

Mình đặt hai file giả lập, không chứa dữ liệu thật:

```text
repo-foundation/references/internal-notes.log
repo-native-refactor/agents/scratch.tmp
```

Các đuôi này bị `.gitignore` hiện tại bỏ qua. Với generator nguyên bản chạy `-AllowDirty`, ZIP chứa cả hai. Để kiểm tra riêng nhánh clean mà không bị R1 che mất, mình sửa duy nhất phép chuẩn hóa output status trong bản thử TEMP và commit thay đổi đó tại fixture. Git status rỗng, generator vẫn đóng gói hai file ignored và ghi `working_tree_clean: true`.

File trong ZIP khớp SHA-256 với manifest chỉ chứng minh payload khớp manifest đã tạo. Nó chưa chứng minh payload thuộc `source_commit`.

Cách sửa phù hợp mục tiêu của Đợt B:

1. Nhánh release lấy bytes từ commit đã chọn, chẳng hạn xuất các đường dẫn được phép từ Git object tree.
2. Giới hạn payload vào LICENSE gốc, SKILL.md/LICENSE của từng skill, các references được quản lý trong commit và metadata thực sự hỗ trợ.
3. Nếu chủ đích chỉ hỗ trợ `agents/openai.yaml`, chọn đúng file đó. Code hiện tại lấy toàn bộ `agents/`, rộng hơn mô tả trong báo cáo.
4. Nhánh scratch có thể giữ riêng, nhưng phải nhận diện rõ là build từ working tree, không dùng làm bằng chứng đã thử đường release.

Test bắt buộc: thêm file ignored vào references/agents nhưng package release không đổi; đối chiếu danh sách và byte payload với commit độc lập với manifest do generator tự sinh.

Không cần blacklist tất cả đuôi file có thể xuất hiện. Xác định nguồn commit và danh sách đường dẫn được phép giải quyết nguyên nhân rõ hơn.

## R3 — P2: timestamp ghi giờ địa phương dưới dạng UTC

Vị trí: `scripts/package-runtime.ps1:116`.

```powershell
generated_at = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')
```

`Get-Date` dùng giờ địa phương, còn `Z` trong format này được ghi nguyên văn. Trên máy UTC+7, gói thử ghi `2026-09-27T00:48:34Z` trong khi UTC thực tế khoảng `2026-09-26T17:48:34Z`.

Dùng UTC thực sự:

```powershell
generated_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
```

Hoặc giữ giờ địa phương nhưng ghi offset tương ứng. Test nên parse timestamp và kiểm tra nó nằm trong khoảng bắt đầu/kết thúc build theo UTC.

## Những gì đã làm đúng

- Có LICENSE ở gốc và trong từng skill.
- Manifest JSON đọc được bằng parser UTF-8 thông thường, không cần xử lý BOM.
- Có đối chiếu file thiếu, sai hash và file thừa sau giải nén.
- Gói runtime nhỏ hơn source repository đầy đủ; payload bình thường không chứa harness.
- Đã thử cài từ ZIP giải nén vào project tạm.
- Nhánh scratch ghi `working_tree_clean: false` khi Git thấy trạng thái dirty.

## Tiêu chí chốt Đợt B đề xuất

1. Sửa R1–R3; có test cho nhánh release sạch, nhánh dirty và file ignored.
2. Giữ bài test giải nén/cài đặt hiện có; thêm đối chiếu với nguồn commit độc lập.
3. Đưa package tests vào CI khi commit Đợt B. Workflow hiện tại chưa chạy suite này.
4. Quy định thư mục output: default `dist/` hiện không có trong `.gitignore`; sau build nó có thể làm lần build tiếp theo bị xem là dirty. Chọn output ngoài repo hoặc xử lý generated output rõ ràng.
5. Ghi hướng dẫn dành cho người tải ZIP: cấu trúc gói, cách kiểm tra và cách đặt hai skill vào project. Bài test hiện dùng installer từ source repo; installer không nằm trong ZIP, vì vậy đừng mô tả bài test đó là trải nghiệm chỉ cần tải ZIP đã hoàn chỉnh.

Không cần đợi Đợt B xong mới thiết kế fixture của hai demo. Tuy nhiên, chưa nên công bố gói ZIP như release đã đạt tiêu chí từ commit nguồn. ZIP cũng là đường phân phối riêng, không tự thay đổi payload của lệnh npx hiện tại.

## Phạm vi thay đổi và log

Không sửa generator, installer, tests hoặc Git history của repo người dùng. Thay đổi chuẩn hóa null để tách R2 chỉ nằm trong fixture TEMP và được ghi rõ trong `results.json`.

Log và fixture tại:

```text
C:\Users\Natch\AppData\Local\Temp\runtime-package-audit-nqr8jdwz
```

Các file chính: `clean-build.log`, `author-suite.log`, `dirty-output.log`, `clean-with-normalization.log`, `results.json`, `run-guarded.ps1`. Wrapper kiểm tra đường dẫn xóa nằm trong vùng thử đã tạo; TEMP/TMP của process thử cũng được giới hạn vào đó. Không xóa thư mục dist hay dữ liệu có sẵn của người dùng.
