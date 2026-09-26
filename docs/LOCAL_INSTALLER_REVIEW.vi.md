# Review thay đổi cài đặt và tài liệu

Ngày kiểm tra: 2026-09-26. Đối tượng: working tree tại `C:\Users\Natch\Desktop\SKILLS-MAIN`, trên HEAD `200286cbb7cb67587b9b4131f9cd001203e51745`, có thay đổi chưa commit. Báo cáo này không phải chứng nhận cho một commit mới đã được phát hành.

## Kết luận

**BLOCK đối với việc phát hành installer PowerShell mới với cam kết cập nhật an toàn/atomic hiện tại.** Lỗi nằm ở `scripts/install-skills.ps1`, không phải nhánh snapshot Python đã được sửa ở các vòng trước. Các kiểm tra harness và archive được chạy trong lượt này đều đạt.

## Những kiểm tra đã thực thi

| Kiểm tra | Kết quả quan sát |
|---|---|
| `python -B -m unittest discover -s repo-foundation/evals/tests -v` | PASS 26/26; 2.657 giây |
| `python -B -m unittest discover -s repo-native-refactor/evals/tests -v` | PASS 33/33; 61.334 giây |
| `python -B repo-foundation/evals/harness.py validate` | PASS 10/10 schema, rubric, policy, 4 task, 7 trusted script với 10 bindings |
| Chạy `scripts/verify-archive.ps1` | PASS 31/31 packets |
| Installer: cài mới vào đường dẫn có dấu | Exit 0; cả hai SKILL.md tồn tại; thiếu cả hai LICENSE |
| Installer: đích đã có skill, không dùng `-Update` | Exit 1; nội dung đích không đổi |
| Installer: nguồn không tồn tại | Exit 1; không tạo `.agents` trong project thử |
| Installer: thiếu references của skill thứ hai | Exit 1; không tạo `.agents` trong project thử |
| Installer: cập nhật bình thường | Exit 0; reference cũ bị loại; có backup |
| Installer: lỗi chép payload sau khi xóa bản cũ | Exit 1; cả hai SKILL.md ở đích đều mất; backup vẫn đọc được |
| GitHub API và trạng thái Git | About có nội dung; topics rỗng; chưa có homepage/Pages; sửa đổi mới còn ở local |

Unit tests và archive verification được chạy trên working tree hiện tại. Lượt này không lặp lại toàn bộ audit fresh-clone với `core.autocrlf=true`, toàn bộ CP2/CP3/CP4, hoặc thử nghiệm hiệu quả skill với model mới. Các kết quả npx trước đó nằm trong [installation checks](npx-install-verification.md); không coi chúng là lần chạy mới của lượt này.

## P1 — Update để lại vị trí cài đặt bị hỏng khi việc chép thất bại

Vị trí: `scripts/install-skills.ps1:129–151`; tuyên bố liên quan tại `README.md:86`.

Installer xóa cả hai skill cũ ở vòng lặp dòng 130–137, rồi mới chép bản mới ở dòng 140–151. Nhánh `finally` chỉ dọn staging; không có nhánh khôi phục đích từ backup khi triển khai thất bại.

Thử nghiệm đã cho `Copy-Item` ném lỗi khi bắt đầu chép `repo-foundation/SKILL.md` vào đích, sau khi backup hoàn tất. Tiến trình trả exit 1, cả Foundation lẫn Refactor đều không còn SKILL.md ở vị trí agent đọc. Backup còn nguyên để phục hồi thủ công: đây không phải bằng chứng mất dữ liệu không thể khôi phục, nhưng là bằng chứng bản cài đang dùng bị phá vỡ khi update lỗi.

Vì vậy, câu “atomic replacement verified” không đúng với implementation và kết quả chạy này. Tạo staging và backup chưa đủ để bảo đảm update thành công toàn bộ hoặc giữ lại bản cũ.

Hướng sửa đề xuất:

1. Chuẩn bị và kiểm tra đầy đủ payload trước khi thay vị trí đang dùng; staging trên cùng volume giúp thực hiện việc đổi tên thư mục mà không phải chép qua volume.
2. Giữ bản cũ nguyên vẹn, theo dõi rõ từng bước thay thế hai skill và hoàn tác khi một bước thất bại.
3. Xác minh trạng thái sau rollback. Nếu rollback cũng lỗi, giữ backup và in đường dẫn cùng hướng dẫn phục hồi cụ thể; không báo thành công.
4. Kiểm tra tình huống lỗi khi thay skill thứ nhất, skill thứ hai, xác minh và phục hồi. Kiểm tra lại hash/file inventory của bản cũ sau mỗi trường hợp cần rollback.
5. Chỉ mô tả những bảo đảm đã thử. Rollback khi exception được xử lý không đồng nghĩa với atomicity khi mất điện, tiến trình bị kill hay hai installer chạy đồng thời.

Nếu chưa muốn duy trì cơ chế này, có thể giữ installer ở chức năng cài mới và từ chối update cho tới khi có kiểm tra phù hợp. Đây là lựa chọn phạm vi sản phẩm, không bắt buộc phải xây transaction phức tạp chỉ để có thêm một cách cài.

## P2 — Payload của installer bỏ sót LICENSE

Vị trí: `scripts/install-skills.ps1:92–104` và `139–151`.

Source của cả hai skill đã có LICENSE nhưng script chỉ chép SKILL.md, references và agents. Cài mới thành công vẫn không có LICENSE trong hai thư mục đã cài. Việc thêm LICENSE vào repo chưa giải quyết được đóng gói bằng script này.

Thêm LICENSE vào danh sách payload ở cả staging lẫn deploy. Kiểm tra file thực sự hiện diện và khớp byte với bản nguồn. Đây là nhận xét tính đầy đủ của gói phân phối, không phải một kết luận pháp lý riêng.

## P2 — Tài liệu nói kiểm tra toàn bộ file, code chỉ kiểm tra hai đường dẫn

Vị trí: `docs/installation.md:128`; implementation tại `scripts/install-skills.ps1:154–165`.

Post-deploy chỉ kiểm tra SKILL.md là file và references là directory. Nó không đối chiếu danh sách references, nội dung file, agents hay LICENSE. Do đó câu “Verifies all files in destination” vượt quá phép kiểm tra thực tế. Nhận xét này dựa trên đọc code; không giả định `Copy-Item` thường xuyên âm thầm bỏ file.

Hoặc thu hẹp câu mô tả cho đúng, hoặc tạo manifest cho payload gồm đường dẫn tương đối và SHA-256, rồi đối chiếu đúng tập file sau triển khai. Nếu dùng manifest, test một file thiếu, một file thay byte và một file thừa trong thư mục skill được quản lý. Không xóa file ở ngoài hai thư mục skill để đạt inventory.

## Phần đã cải thiện

- Lệnh kiểm tra archive tập trung trong một script, kiểm số verifier và exit code; đã chạy đạt 31/31.
- Installer kiểm tra cả hai nguồn trước khi đụng đích; hai ca nguồn hỏng đã xác nhận hành vi này.
- Không có `-Update` thì từ chối ghi đè bản đang dùng.
- Update bình thường loại được reference cũ và tạo backup.
- README/BENCHMARK đã bớt lời quảng bá và phân biệt việc kiểm archive với việc chạy lại thí nghiệm.

CI hiện gọi archive script và harness tests nhưng chưa có test cho installer PowerShell. Nên thêm kiểm tra installer sau khi sửa, để lỗi tương tự có tín hiệu thất bại trong CI.

## Ghi chú câu chữ và giới hạn

`repo-native-refactor/SKILL.md:3` vẫn có “regression-free refactoring”, dòng 13 vẫn có các mục tiêu “Zero ...”. Các dòng nguyên tắc có thể được hiểu là yêu cầu, nhưng description được hiển thị ngoài ngữ cảnh có thể bị đọc thành lời bảo đảm. Đề xuất description dùng “behavior-preserving refactoring with verification”; nguyên tắc nêu giữ hành vi được phép, kiểm tra rủi ro hồi quy và báo giới hạn xác minh. Không cần sửa luồng chọn skill chỉ để chèn từ khóa SEO.

## Dấu vết thử nghiệm cục bộ

Fixture, wrapper chèn lỗi và log được lưu tại:

```text
C:\Users\Natch\AppData\Local\Temp\skills-install-review-2ce0lb5s
```

- `results.json`: kết quả sáu tình huống.
- `invoke-checked.ps1`: wrapper chặn xóa ngoài khu vực thử và chèn lỗi Copy-Item có kiểm soát.
- `injected-failure.log`: log backup đã tạo, sau đó exception triển khai.
- `failure-backup`: bản cài cũ còn để kiểm tra khả năng phục hồi.

Phép chèn lỗi dùng wrapper trong process thử, không sửa code installer. Mọi target bị xóa trong các probe đều bị kiểm tra giới hạn vào thư mục thử hoặc staging của installer trong TEMP. Không dùng project thật của người dùng làm đích thử. TEMP là bằng chứng làm việc tại máy này, không phải archive lâu dài của repository.
