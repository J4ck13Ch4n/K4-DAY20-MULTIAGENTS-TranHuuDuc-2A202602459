# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Trần Hữu Đức | 2A202602459 | Toàn bộ lab (harness, thí nghiệm, báo cáo) |

- Mô hình: `gpt-4o-mini` qua cổng tương thích OpenAI `https://api.shopaikey.com/v1` (map vào `AZURE_OPENAI_*` theo `model.py` option 1), `LAB_TEMPERATURE=0`, `recursion_limit=60` (riêng lần chạy lại `skills-auto/data-learn` dùng 40 để chặn vòng lặp tốn token).
- Phiên bản Deep Agents: 0.7.21, hệ điều hành: Linux (WSL), chạy trực tiếp (không Docker).
- Số lần chạy tác vụ đã dùng: baseline 3 learn + subagents 3 learn + skills-auto 3 learn (+2 chạy lại do lỗi hạ tầng) trước freeze; sau freeze chạy thêm baseline 3 eval + subagents 3 eval + skills-auto 6 all.
- Commit của tag `freeze`: (điền sau khi tag, xem `git rev-parse freeze`)

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Trên tác vụ đánh giá, `subagents` đạt điểm tương đương `baseline` (không cải thiện), vì trên cả 3 tác vụ học `subagent_calls=0` — tác tử chính tự làm, không giao việc dù có `SUBAGENTS_NOTE`. Token có thể chênh lệch do nhiễu chứ không do giao việc. Căn cứ: mục 5; tổng quan multi-agent của Anthropic ghi nhận chi phí cao mà lợi ích chỉ khi task đủ lớn để chia việc.
- H2 (skills-auto so với baseline): Trên tác vụ đánh giá, `skills-auto` cải thiện tối đa 1-2 check quy ước cũ (nếu `skills_read>0`), nhưng không vượt trội vì (a) skill do model tự sinh thường không có lợi trung bình (SkillsBench: skill người viết +16pp, skill tự sinh ~0), (b) lợi ích trên tác vụ học thường không chuyển sang tác vụ mới do quá khớp (SkillEvolBench), (c) ở Phần 3.4 `skills_read=0` và 2/3 lần chạy lỗi hạ tầng. Căn cứ: mục 4 (9/19 check thất bại thuộc nhóm E) + mục 6.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm tác vụ đánh giá thấp hơn hoặc bằng tác vụ học ở mọi điều kiện, vì tác vụ đánh giá khác dữ liệu và thêm một quy ước mới mà skill học từ tác vụ học không bao phủ. Chênh lệch learn-eval của `skills-auto` lớn hơn của `baseline` là dấu hiệu quá khớp.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có các công cụ: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep` (nhóm tệp), `execute` (shell), `task` (subagent). Công cụ cho phép chạy lệnh là `execute`.
2. Mô tả của công cụ `task` nói subagent `general-purpose` là agent đa năng cho nghiên cứu/tìm kiếm/nhiệm vụ nhiều bước, có toàn quyền công cụ như tác tử chính; mỗi lần gọi là stateless mặc định — subagent chỉ nhìn thấy prompt mà tác tử chính gửi và trả về một báo cáo cuối, báo cáo không hiện cho user.
3. System prompt mặc định rỗng (`''`). Một câu hành vi từ mô tả `task`: "Each invocation is stateless by default: the agent sees only the prompt you give it and returns a single final report." Một câu từ mô tả `execute`: "Executes a shell command in an isolated sandbox and returns combined stdout/stderr with the exit code (truncated if very large)."

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

Chỉ dùng tác vụ học, kết quả `baseline` (code-learn 5/10, data-learn 2/8, logs-learn 1/9; `check_breakdown.py`: technical 8/18, house rules 0/9).

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | parse_price_all_formats | D. Bỏ sót định dạng | `wrong for: ['(12.00)']` — thiếu định dạng ngoặc đơn |
| code-learn | csv_quoting_follows_docstring | A. Bỏ qua đặc tả | `to_csv_row returned 'Desk, large "oak",10.00,2'` — không đối chiếu docstring về quoting |
| code-learn | rule_type_hints | E. Vi phạm quy ước | `RULE: every public function ... has type annotations ...` |
| code-learn | rule_regression_tests | E | `RULE: add tests/test_regressions.py with one test function per bug ...` |
| code-learn | rule_changelog | E | `RULE: record each fix in CHANGELOG.md under '## Unreleased' as '- fix(<function name>): ...'` |
| data-learn | north_q1_revenue | D | `wrong value (got 245.28)` — tính sai do chưa xử lý trùng/-999/múi giờ/format ngày |
| data-learn | north_q1_orders | D | `wrong value (got 3)` |
| data-learn | duplicate_rows_removed | D | `wrong value (got 0)` — không khử trùng |
| data-learn | rule_money_in_cents | E | `RULE: money values in answer.json are integer cents (1606.67 USD is written 160667).` |
| data-learn | rule_meta_block | E | `RULE: answer.json has an object meta = {... rows_in ... rows_used ...}` |
| data-learn | rule_clean_csv | E | `RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; ...` |
| logs-learn | entry_count | D | `wrong number of entries (got 10)` — chưa gộp stack trace nhiều dòng/dòng lặp |
| logs-learn | timestamps_utc | D | `4/25 timestamps match` — sai chuẩn hóa múi giờ/định dạng |
| logs-learn | exception_fields | D | `22 wrong exception values` |
| logs-learn | repeat_counts | D | `21 wrong repeat_count values` |
| logs-learn | counts_by_service | D | `counts_by_service: wrong values` |
| logs-learn | rule_service_names | E | `RULE: service names ... lower-case with '-' replaced by '_' ...` |
| logs-learn | rule_sorted_errors | E | `RULE: errors is sorted by service, then by timestamp_utc, ascending.` |
| logs-learn | rule_schema_header | E | `RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage".` |

Nhận xét: tổng 19 check thất bại gồm 10 kỹ thuật (A/D) và 9 quy ước (E) — không có nhóm nào chiếm đa số tuyệt đối. Với `gpt-4o-mini`, cả hai nhóm đều fail (technical chỉ đạt 8/18), khác kỳ vọng "mô hình mạnh chỉ fail E". Skill có thể phòng ngừa nhóm E hiệu quả nhất vì E là quy ước Acme ổn định, diễn đạt được thành checklist (`detail` bắt đầu bằng `RULE:`); nhóm D cũng có thể viết thành checklist nhưng dễ quá khớp vào dữ liệu cụ thể của tác vụ học.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế): `explorer` (đọc đề/docstring/mẫu dữ liệu, chỉ báo cáo sự thật, không sửa — tách bước hiểu đề để tránh lỗi A); `implementer` (thực hiện sửa + chạy test/script và báo cáo — tách bước làm để dễ kiểm chứng, tránh lỗi B/C); `reviewer` (kiểm tra độc lập theo đề và biên, không sửa — bắt lỗi trước khi kết thúc, tránh lỗi B/F). `description` viết dạng hành động ("Use when ... delegate to ... with ..."), `build_agent` tự nối `PATHS_NOTE` vào `system_prompt` mỗi subagent.
- `subagent_calls` ở từng tác vụ và nhận xét: code-learn 0, data-learn 0, logs-learn 0 (xem `run.json`). Đây là kết quả hợp lệ: tác vụ nhỏ, tác tử chính tự làm hết; mô tả `task` nhấn mạnh `general-purpose` mặc định nên subagent tự định nghĩa kém nổi bật; `SUBAGENTS_NOTE` chỉ khuyến khích chứ không bắt buộc.
- Thông tin khi giao việc: không có lần giao việc nào nên không đánh giá được thiếu/thừa; vết chỉ có luồng chính, không thấy nội dung bên trong subagent.
- Ảnh hưởng đến token và thời gian: mean tokens/learn: baseline 57,120 vs subagents 36,156 (code 48,572→61,118 tăng; data 103,234→26,732 giảm mạnh; logs 19,556→20,620 tương đương). Vì `subagent_calls=0`, chênh lệch hoàn toàn do nhiễu của model/gateway, không phải chi phí giao việc. Thời gian tương tự (baseline data 253.6s vs subagents data 26.2s — nhiễu lớn).

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: 1 lần (`python -m lab.curator`), ghi 3 skill, xóa 0 skill (giữ nguyên đầu ra curator, không sửa tay). Lý do giữ: cả 3 đều qua `validate_skill`, không chứa eval marker, nội dung khớp `detail` của tác vụ học.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| check-type-annotations | Tổng quát (mọi package Python, không nêu tên hàm/tệp cụ thể) | Đúng, khớp `RULE: ... type annotations ...` của code-learn | 6 dòng checklist; `description`: "Use this skill to ensure all public functions have type annotations ..." (nêu tình huống kích hoạt, hơi hẹp nhưng chấp nhận được); `skills_read` Phần 3.4 = 0 (chung cả 3 skill, không skill nào được đọc ở logs-learn sạch; 2 task còn lại lỗi hạ tầng) |
| validate-changelog | Tổng quát ở mức quy ước Acme (`CHANGELOG.md`, `## Unreleased`, `- fix(...): ...` là tên quy ước được phép) nhưng фикси 3 bullets có thể quá khớp số lượng của tác vụ học | Đúng với `detail` code-learn, nhưng quy tắc "ít nhất 3 bullets" có thể sai trên tác vụ mới có số fix khác | 6 dòng; `description` nêu khi document changes (rõ); `skills_read`=0 như trên |
| ensure-csv-format | Nửa tổng quát: header `order_id,timestamp_utc,region,amount_cents` và canonical region là quy ước Acme (được phép), nhưng liệt kê cứng header dễ thành học vẹt nếu eval đổi schema | Đúng với `RULE: write workspace/clean.csv ...` của data-learn | 7 dòng; `description`: "Use this skill to confirm that CSV outputs adhere ..." (đủ rộng để kích hoạt); `skills_read`=0 |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

(Tạm thời trước freeze — sẽ dán `report/table.md` và `check_breakdown.py` sau khi chạy eval.)

```text
(dán bảng ở đây sau Phần 4.3)
```

Các lần chạy có `error` ở Phần 3.4: `skills-auto/code-learn` `OpenAITimeoutError: Request timed out` (2 lần liên tiếp, tokens 6,244, `tool_calls`=0 do `messages=[]` khi lỗi — hạn chế đã nêu trong pseudocode 03); `skills-auto/data-learn` `GraphRecursionError` (limit 60: 375,312 tokens; limit 40: 184,382 tokens). `skills_modified=false` mọi lần chạy. Cách xử lý: chạy lại 1 lần mỗi task; timeout vẫn lặp lại nên giữ nguyên để phân tích (lỗi hạ tầng, không dùng làm bằng chứng lỗi tác tử); recursion giảm xuống 40 để chặn đốt token và ghi chú trong báo cáo.

## 8. Phân tích

(Sẽ hoàn thiện sau eval. Bản nháp: so sánh learn/eval, tách technical vs rule_, giải thích 1 check giúp được và 1 check không, chi phí token/điểm, rò rỉ/quá khớp, nhiễu learn Phần 3.4 vs sau freeze.)

1. (chờ bảng eval)
2. (chờ breakdown sau freeze)
3. (chờ vết + skills_read eval)
4. (chờ mean tokens đủ 3 điều kiện)
5. Không phát hiện rò rỉ eval marker trong skill (`validate_skill` + `eval_markers()` đã chặn; kiểm tra tay không thấy id tác vụ eval, tên tệp eval, đáp án hay con số cụ thể). Nguy cơ quá khớp: `validate-changelog` cứng "ít nhất 3 bullets", `ensure-csv-format` cứng header — phòng tránh bằng cách không đưa dữ liệu eval vào prompt curator (chỉ role==learn), không sửa tay skill, và đánh giá tổng quát ở mục 6.
6. Nhiễu: điểm learn cùng bộ skill ở Phần 3.4 (đã sao lưu `results/skills-auto-dev`) so với sau đóng băng — sẽ điền sau khi chạy lại. Hai lần chạy `skills-auto/data-learn` đã cho thấy nhiễu lớn về token (375k vs 184k chỉ do đổi limit) và điểm ổn định ở 0/8 khi lỗi.

## 9. Hạn chế và tính hợp lệ

1. Chỉ 3 tác vụ mỗi vai trò (tổng 6): mẫu quá nhỏ, một check đảo chiều đã đổi 10-12% điểm; không thể kết luận thống kê, mọi chênh lệch nhỏ đều có thể là nhiễu.
2. Mỗi cấu hình chạy một lần (trừ 2 lần rerun lỗi): nhiễu model/gateway rất lớn (data-learn baseline 103k vs subagents 26k tokens; cùng skill chạy lại vẫn timeout) nên không ước lượng được phương sai.
3. Chỉ một mô hình (`gpt-4o-mini` qua gateway thứ ba): hành vi (không delegate, không đọc skill, lặp recursion) có thể do model/gateway, không khái quát sang model khác; timeout liên tiếp ở `skills-auto/code-learn` gợi ý vấn đề hạ tầng hơn là khoa học.
4. Tác vụ do giảng viên thiết kế với quy ước Acme ẩn: skill học được thực chất là "đoán quy ước ẩn" từ `detail`, dễ quá khớp và khó chuyển sang quy ước mới của eval.

## 10. Kết luận

(Chờ số eval; tối đa 5 câu, chỉ khẳng định điều số liệu hỗ trợ, kèm 1 đề xuất cải tiến.)

## Phụ lục

- Lệnh đã chạy (theo thứ tự): `pip install -e .`, `pytest tests/test_01_provided.py`, `python -c "from lab.model import make_model; ..."`, `python scripts/tour.py`, `pytest tests/`, `python -m lab.runner --condition baseline --tasks data-learn`, `python -m lab.runner --condition baseline --tasks code-learn logs-learn`, `python -m lab.runner --condition subagents --tasks learn`, `python -m lab.curator`, `python -m lab.runner --condition skills-auto --tasks learn`, rerun 2 task lỗi, `python scripts/check_breakdown.py`.
- Thử thách mở rộng (nếu có): chưa chọn — đề xuất 6e (lặp để đo nhiễu) nếu còn ngân sách, hoặc 6b (vòng tiến hóa thứ hai) để quan sát skill bloat.
- Ghi chú khác: `.env` đã chuẩn hóa từ `CUSTOM_*` sang `AZURE_OPENAI_*` (Option 1 cổng tương thích OpenAI) để khớp `model.py` mà không sửa code có sẵn; backup ở `.env.bak`.
