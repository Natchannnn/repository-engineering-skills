# Review tiếp theo Đợt B: generator đã sửa, acceptance suite còn hai điểm

Ngày kiểm tra: 2026-09-27. Working tree trên commit `d4776c42c183cd7c4a00b5e3511db59aa7c523f2`; thay đổi Đợt B chưa commit.

## Kết luận

Đóng ba finding R1–R3 của lượt trước trong phạm vi đã thử. Generator nguyên bản hiện build thành công từ fixture sạch, payload khớp byte với commit, file ignored không lọt vào release và UTC timestamp đúng.

**Chưa chốt Đợt B vì acceptance suite còn lỗi tương thích PowerShell và phép so sánh với commit chưa được thực hiện.** Hai sửa đổi này tập trung ở `scripts/test-package.ps1`; không cần thiết kế lại generator hay đổi kế hoạch demo.

## Bằng chứng chạy

| Kiểm tra | Kết quả |
|---|---|
| Generator hiện tại, fixture Git sạch, không AllowDirty | PASS |
| Inventory payload so với file được phép trong commit | PASS, 17/17 |
| So sánh ZIP bytes trực tiếp với `git cat-file blob` bằng Python | PASS toàn bộ 17 file |
| So sánh SHA-256 với manifest | PASS |
| UTC timestamp nằm trong cửa sổ build | PASS |
| File ignored giả lập trong references không lọt vào release | PASS |
| Suite nguyên bản chạy qua PowerShell 7.6.5 | FAIL ở Test 2: DateTime không có EndsWith |
| Suite trên bản thử chỉ điều chỉnh xử lý DateTime | PASS 7/7 |
| Cùng suite đã điều chỉnh DateTime, generator bị cố ý chèn thêm byte không thuộc commit vào SKILL.md trước khi tạo manifest | **Vẫn PASS 7/7** |
| `git diff --check` | PASS |

Nhánh test bị sửa và generator cố ý làm sai chỉ tồn tại trong TEMP. Không chỉnh code thật để tạo ra các kết quả trên. Phép so sánh độc lập dùng bytes từ Git làm nguồn kỳ vọng, không lấy manifest tự sinh làm bằng chứng về nguồn commit.

## T1 — P1: suite lỗi với kiểu DateTime từ JSON trên PowerShell 7

Vị trí: `scripts/test-package.ps1:77–78`.

Sau `ConvertFrom-Json`, trường timestamp trên PowerShell 7.6.5 ở máy này là `System.DateTime`. Dòng `$tsString.EndsWith("Z")` giả định nó luôn là string nên lỗi:

```text
Method invocation failed because [System.DateTime] does not contain a method named 'EndsWith'.
```

Workflow mới gọi suite với `shell: pwsh`. Vì vậy không thể dùng kết quả chạy bằng `powershell.exe` để khẳng định cùng suite đã đạt dưới pwsh. Chưa chạy remote CI trong lượt này; kết luận lỗi môi trường dựa trên PowerShell 7.6.5 tại máy.

Cách sửa: xử lý rõ trường hợp JSON parser trả string hoặc DateTime, hoặc dùng một parser có hành vi nhất quán cho bài kiểm tra. Tách việc kiểm tra định dạng UTC trong JSON gốc và việc so sánh thời điểm thực tế. Không chỉ ép DateTime thành string theo locale rồi tiếp tục đòi hậu tố Z.

Nghiệm thu: chạy nguyên suite bằng đúng pwsh dùng trong CI; nếu tuyên bố hỗ trợ Windows PowerShell 5.1 thì thử riêng môi trường đó.

## T2 — P2: Test 3 chưa so sánh file với Git blob

Vị trí: `scripts/test-package.ps1:100–113`.

Test ghi kết quả `git cat-file` vào `$tempGitBlob`, nhưng không đọc lại file này và không so sánh hash/bytes của nó với payload. Điều kiện duy nhất đang kiểm tra là `$localHash -ne $expectedHash`, trong đó `$expectedHash` lấy từ manifest do chính generator tạo.

Đây là phép đối chiếu ZIP với manifest, không phải đối chiếu với commit như tên test và thông báo PASS.

Probe kiểm chứng:

1. Sao chép generator và suite vào vùng thử.
2. Điều chỉnh duy nhất cách xử lý DateTime trong suite để Test 2 không che khuất Test 3.
3. Cho generator thêm dòng `NEGATIVE_CONTROL_NOT_IN_SOURCE_COMMIT` vào Foundation SKILL.md ở staging, ngay trước bước tạo manifest.
4. Chạy suite. Toàn bộ bảy test vẫn PASS, bao gồm thông báo đã xác minh với Git objects.

Cách sửa: lấy Git blob dưới dạng bytes và so sánh trực tiếp với file đã giải nén. Ví dụ ý tưởng cho helper Python:

```python
blob = subprocess.run(
    ["git", "-C", repo, "cat-file", "blob", f"{commit}:{git_path}"],
    check=True,
    stdout=subprocess.PIPE,
).stdout
assert extracted_file.read_bytes() == blob
```

Không dùng `text=True`. Cũng không đơn giản thêm hash của file tạo bằng `>` trong Windows PowerShell 5.1: redirection qua shell có thể biến đổi encoding/line endings. Helper xử lý bytes tránh vấn đề đó.

Ngoài so byte, đối chiếu tập đường dẫn kỳ vọng từ commit với tập payload để không chỉ xác minh những file generator đã chọn đưa vào manifest. Phép thử âm tính phải thất bại khi generator thay byte nhưng đồng thời tính lại manifest hợp lệ.

## Phần đã đạt và có thể giữ

- Xử lý output Git status rỗng đã sửa đúng.
- Release sử dụng commit object tree, khác với scratch build.
- Payload mặc định hiện tại khớp đúng nguồn Git trong phép kiểm tra độc lập.
- Timestamp UTC được sửa đúng.
- `dist/` đã được ignore và workflow đã thêm package suite.
- Tài liệu đã có cấu trúc ZIP, bước kiểm tra hash và hướng dẫn copy thủ công.

Việc đóng R1–R3 là kết luận về các vấn đề cụ thể đã kiểm tra, không phải lời bảo đảm mọi cấu trúc repository/đường dẫn/phiên bản shell đều đã thử.

## Điều kiện chốt ngắn gọn

1. Sửa T1, chạy suite trên pwsh.
2. Sửa T2 và thêm negative control: payload sai byte so với Git phải FAIL ngay cả khi manifest khớp payload.
3. Giữ kết quả các ca clean build, dirty rejection, ignored isolation, UTC và consumer installation hiện có.
4. Chốt commit Đợt B rồi kiểm tra CI trên chính commit đó trước khi mô tả release là đã qua CI.

Không cần chạy lại toàn bộ lịch sử audit để sửa hai phép kiểm tra này. Hai demo có thể tiếp tục được thiết kế theo kế hoạch đã duyệt.

## Log và giới hạn môi trường

```text
C:\Users\Natch\AppData\Local\Temp\runtime-rereview-_v929dws
```

Các file chính: `results.json`, `original-suite.log`, `independent-build.log`, `original-suite-date-normalized.log`, `mutated-payload-suite-date-normalized.log`. Fixture độc lập cùng ZIP được giữ để kiểm tra lại.

Một số lần thử gọi lồng Windows PowerShell 5.1 trong môi trường công cụ này dừng do không tìm thấy Get-FileHash; nguyên nhân môi trường chưa được xác định. Không dùng các lần đó để kết luận lỗi sản phẩm hoặc phủ nhận báo cáo 5.1 của tác giả. Lỗi DateTime nêu ở T1 tái hiện được riêng trên pwsh; các phép thử dùng bản sửa DateTime chạy hoàn tất trên cùng đường gọi đó.

Không sửa generator, suite hoặc workflow thật, không commit/push. Chỉ thêm báo cáo này. Các lệnh xóa trong vùng thử được giới hạn vào thư mục TEMP thuộc probe; không xóa output hay dữ liệu có sẵn của người dùng.
