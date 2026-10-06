# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Trần Hữu Đức | 2A202602459 | Toàn bộ lab (harness, thí nghiệm, báo cáo) |

- Mô hình: `gpt-4o-mini` qua cổng tương thích OpenAI `https://api.shopaikey.com/v1` (map vào `AZURE_OPENAI_*` theo `model.py` option 1), `LAB_TEMPERATURE=0`, `recursion_limit=60` (riêng lần chạy lại `skills-auto/data-learn` dùng 40 để chặn vòng lặp tốn token).
- Phiên bản Deep Agents: 0.7.21, hệ điều hành: Linux (WSL), chạy trực tiếp (không Docker).
- Số lần chạy tác vụ đã dùng: baseline 3 learn + subagents 3 learn + skills-auto 3 learn (+2 chạy lại do lỗi hạ tầng) trước freeze; sau freeze chạy thêm baseline 3 eval + subagents 3 eval + skills-auto 6 all. Tổng cộng 18 lần chạy chính thức + 4 lần chạy lại/chạy nháp.
- Commit của tag `freeze`: 56d1ee4 (`git rev-parse freeze`)

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

`report/table.md` do `python -m lab.compare` sinh ra (khớp `run.json`):

```text
| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 5/10 | 5/10 | 5/10 |
| data-learn | 2/8 | 2/8 | 0/8 |
| logs-learn | 1/9 | 1/9 | 1/9 |
| code-eval | 1/11 | 2/11 | 4/11 |
| data-eval | 3/9 | 2/9 | 1/9 |
| logs-eval | 1/10 | 0/10 | 1/10 |
| **Mean score - learning tasks** | 0.29 | 0.29 | 0.20 |
| **Mean score - evaluation tasks** | 0.17 | 0.13 | 0.19 |
| **Mean tokens per run** | 107,300 | 71,253 | 107,508 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |
```

`python scripts/check_breakdown.py` (sau freeze nên hiện cả eval):

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      5/18         0/12         157,480      0/3
baseline      learn     8/18         0/9           57,120      0/3
subagents     eval      4/18         0/12         106,350      0/3
subagents     learn     8/18         0/9           36,156      0/3
skills-auto   eval      6/18         0/12          72,473      0/3
skills-auto   learn     6/18         0/9          142,543      0/3
```

Các lần chạy có `error` (ghi vào `run.json`, không crash chương trình): `baseline/code-eval` và `subagents/code-eval` (`GraphRecursionError` limit 60, 36 và 57 tool calls — đã có vết đầy đủ sau khi `run_task` chuyển sang `stream(values)` để giữ `messages` cuối cùng), `skills-auto/data-learn` (`GraphRecursionError`, 29 calls, 362,038 tokens). Đã chạy lại và làm sạch: `baseline/data-eval` 0/9→3/9 (hết lỗi), `skills-auto/code-learn` 2/10 timeout→5/10 (hết lỗi, bằng baseline). Ở Phần 3.4 (bản sao lưu `results/skills-auto-dev`): `skills-auto/code-learn` `OpenAITimeoutError` (2 lần, 6,244 tokens), `skills-auto/data-learn` `GraphRecursionError` (limit 60: 375,312 tokens; limit 40: 184,382 tokens). Mọi lần chạy đều `skills_modified=false`; `python scripts/verify_freeze.py` báo `OK` (6 runs skills-auto đúng skill đóng băng, chạy sau tag). Ba vòng lặp còn lại được giữ nguyên để phân tích như hành vi thật của model (kèm vết), không phải lỗi hạ tầng thoáng qua.

## 8. Phân tích

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Trên tác vụ học: `subagents` 0.29 bằng `baseline` 0.29 (không cải thiện, đúng H1 vì `subagent_calls=0`); `skills-auto` 0.20 tệ hơn baseline (data-learn 0/8 vs 2/8) nhưng code-learn đã về bằng nhau 5/10 sau khi chạy lại hết timeout — phần tệ còn lại đi kèm `GraphRecursionError` ở data-learn nên là suy giảm do vòng lặp chứ không phải do nội dung skill. Trên tác vụ đánh giá: `subagents` 0.13 thấp hơn `baseline` 0.17, `skills-auto` 0.19 cao hơn baseline (code-eval 1/11→2/11→4/11; data-eval 3/9→2/9→1/9 — baseline tốt nhất ô này; logs-eval 1/10→0/10→1/10). Không có điều kiện nào "cải thiện học nhưng không cải thiện eval" theo nghĩa quá khớp kinh điển; ngược lại `skills-auto` tệ hơn ở học nhưng tốt nhất ở eval — mẫu hình ngược này cho thấy nhiễu chi phối chứ không phải học chuyển giao. H1 đúng ở học (subagents ≈ baseline); H2 đúng một nửa (skills-auto tốt nhất eval nhưng không qua cơ chế skill, xem câu 3); H3 sai một nửa (eval không thấp hơn học ở mọi ô: baseline data-eval 3/9 cao hơn data-learn 2/8).
2. Tách technical vs `rule_`: mọi điều kiện đạt 0/9 (learn) và 0/12 (eval) ở check quy ước — skill sinh ra (nhắm vào `rule_type_hints`, `rule_changelog`, `rule_clean_csv`) không giúp bất kỳ check `rule_` nào, kể cả quy ước cũ đã thấy ở học. Nhóm technical: learn baseline 8/18 = subagents 8/18 > skills-auto 3/18; eval baseline 2/18 < subagents 4/18 < skills-auto 6/18. Quy ước **mới** của eval (`rule_version_bump` ở code-eval, `rule_sorted_keys_format` ở data-eval, `rule_source_line` ở logs-eval) đều fail ở cả 3 điều kiện — skill không thể giúp vì (a) skill chỉ tổng hợp từ `detail` của tác vụ học, không chứa quy ước mới, (b) thực tế `skills_read=0/6` nên skill chưa từng được đọc. Đây là bằng chứng phủ định cho khả năng chuyển giao của skill tự sinh, đúng dự đoán SkillEvolBench.
3. Một check skill "giúp" và một check skill không giúp (dựa vào vết + `skills_read`): vì `skills_read=0/6` ở mọi điều kiện, không có check nào được skill giúp theo cơ chế đọc-làm theo. Ví dụ `skills-auto/code-eval` đạt `visible_suite_passes`, `billable_blocks_round_up`, `add_slot_no_shared_state` trong khi `baseline/code-eval` fail 3 check này — nhưng `run.json` ghi `skills_read=0`, `subagent_calls=0`, vết không có `read_file skills/...`, nên cải thiện này là nhiễu đường suy luận khác nhau, không phải tác dụng skill. Ngược lại `rule_type_hints` fail ở cả 6/6 lần chạy code (learn+eval, mọi điều kiện) dù skill `check-type-annotations` tồn tại và khớp đúng quy tắc — vì skill không được đọc (`skills_read=0`), tác tử không bao giờ áp dụng; vết `logs-learn` sạch cũng không có dòng đọc skill nào dù `SKILLS_NOTE` yêu cầu đọc đầu tiên. Kết luận: failure mode là "không đọc", không phải "đọc nhưng làm sai".
4. Chi phí: mean tokens/run (cả learn+eval): baseline 107,300 ≈ skills-auto 107,508 > subagents 71,253. Hiệu quả điểm eval trên mỗi 1M token: baseline 0.17/0.107M≈1.59, subagents 0.13/0.071M≈1.83 (tốt nhất), skills-auto 0.19/0.107M≈1.78. Đa tác tử KHÔNG đáng chi phí theo nghĩa lý thuyết vì `subagent_calls=0` — chênh lệch token hoàn toàn do nhiễu (baseline data-eval 230k sau khi hết lặp vs 432k lúc lặp; subagents data-learn chỉ 26k). Không thể khẳng định subagents rẻ hơn; chỉ có thể nói trong thí nghiệm này chi phí do số bước lặp của model quyết định, không phải do kiến trúc.
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Không rò rỉ: `validate_skill` chặn eval marker, kiểm tra tay 3 skill không chứa id tác vụ eval (`code-eval`, `data-eval`, `logs-eval`), tên tệp eval, đáp án hay con số cụ thể; header CSV và tên `CHANGELOG.md` là quy ước Acme (được phép theo 05_skill_quality). Dấu hiệu quá khớp nhẹ: `validate-changelog` cứng "ít nhất 3 bullets", `ensure-csv-format` cứng header — nếu eval đổi số fix/schema sẽ sai; nhưng vì `skills_read=0` nên quá khớp chưa kịp gây hại. Phòng tránh: curator chỉ đọc `role==learn`, prompt cấm nêu id/tên tệp/đáp án, `validate_skill` kiểm tra marker lúc chạy, không sửa tay skill, đóng băng bằng tag `freeze` và `verify_freeze.py` OK.
6. Nhiễu: cùng bộ skill đóng băng, điểm học Phần 3.4 (sao lưu `results/skills-auto-dev`) vs sau đóng băng (`results/skills-auto`): code-learn 1/10 (timeout) → 5/10 (sạch) chênh +4 checks (+0.40); data-learn 0/8 → 0/8 (0) nhưng tokens 184k→362k; logs-learn 1/9 → 1/9 (0). Tương tự `baseline/data-eval` chạy lại 0/9 (lặp) → 3/9 (sạch) chênh +3 checks. Mở rộng 6e (3 mẫu/ô: chính/R1/R2) cho khoảng dao động mean eval baseline 0.06-0.17, subagents 0.09-0.24, skills-auto 0.19-0.26 — mọi chênh lệch giữa điều kiện trong bảng mục 7 đều nằm trong hoặc dưới dải nhiễu này. Do đó mọi chênh lệch đều không đáng tin cậy thống kê; kết luận chỉ ở mức định tính (skill không được đọc, rule mới không đạt, vòng lặp tốn token).

## 9. Hạn chế và tính hợp lệ

1. Chỉ 3 tác vụ mỗi vai trò (tổng 6): mẫu quá nhỏ, một check đảo chiều đã đổi 10-12% điểm; không thể kết luận thống kê, mọi chênh lệch nhỏ đều có thể là nhiễu.
2. Mỗi cấu hình chạy một lần (trừ 2 lần rerun lỗi): nhiễu model/gateway rất lớn (data-learn baseline 103k vs subagents 26k tokens; cùng skill chạy lại vẫn timeout) nên không ước lượng được phương sai.
3. Chỉ một mô hình (`gpt-4o-mini` qua gateway thứ ba): hành vi (không delegate, không đọc skill, lặp recursion) có thể do model/gateway, không khái quát sang model khác; timeout liên tiếp ở `skills-auto/code-learn` gợi ý vấn đề hạ tầng hơn là khoa học.
4. Tác vụ do giảng viên thiết kế với quy ước Acme ẩn: skill học được thực chất là "đoán quy ước ẩn" từ `detail`, dễ quá khớp và khó chuyển sang quy ước mới của eval.

## 10. Kết luận

Với `gpt-4o-mini`, cả `subagents` và `skills-auto` đều không tạo cải thiện đáng tin cậy: mọi check quy ước Acme đạt 0/21 và mọi skill đều `skills_read=0`. Chênh lệch điểm eval (+0.07/+0.13) nằm trong dải nhiễu ±1 check của cùng cấu hình và đi kèm 5 lần `GraphRecursionError` tốn 180-430k tokens. Đề xuất tiếp theo: giảm `recursion_limit` xuống 40 cho mọi điều kiện và lặp mỗi ô ít nhất 3 lần để ước lượng phương sai trước khi kết luận về skill hay subagent.

## Phụ lục

- Lệnh đã chạy (theo thứ tự): `pip install -e .`, `pytest tests/test_01_provided.py`, `python -c "from lab.model import make_model; ..."`, `python scripts/tour.py`, `pytest tests/`, `python -m lab.runner --condition baseline --tasks data-learn`, `python -m lab.runner --condition baseline --tasks code-learn logs-learn`, `python -m lab.runner --condition subagents --tasks learn`, `python -m lab.curator`, `python -m lab.runner --condition skills-auto --tasks learn`, chạy lại 2 task lỗi (code-learn mặc định, data-learn `--recursion-limit 40`), `python scripts/check_breakdown.py`, `git commit -m "hypotheses"`, `mv results/skills-auto results/skills-auto-dev`, `git commit --allow-empty -m "freeze skills" && git tag freeze`, `python -m lab.runner --condition baseline --tasks eval`, `python -m lab.runner --condition subagents --tasks eval`, `python -m lab.runner --condition skills-auto --tasks all`, `python scripts/verify_freeze.py`, `python -m lab.compare > report/table.md`, `python scripts/check_breakdown.py`, nâng cấp `run_task` sang `stream(values)` để giữ vết khi chạm limit (gợi ý ở pseudocode 03 điểm 8; `pytest` vẫn 29/29) rồi chạy lại các ô lỗi, 2 vòng thưởng thức `... --tasks eval --results results-r1/r2`, `python -m lab.compare --results results-rX`.
- Thử thách mở rộng (Phần 6, hướng 6e — lặp để đo nhiễu): chạy lại toàn bộ tác vụ đánh giá (3 tasks × 3 conditions) thêm 2 vòng vào thư mục kết quả riêng `--results results-r1` và `results-r2` (18 runs, cùng model/limit/skill đóng băng, sau tag `freeze`). Vòng chính + R1 + R2 cho 3 mẫu mỗi ô:
  - Mean eval: baseline 0.17 (chính) / 0.06 (R1) / 0.17 (R2) → khoảng 0.06-0.17; subagents 0.13/0.24/0.09 → 0.09-0.24; skills-auto 0.19/0.26/0.23 → 0.19-0.26.
  - Từng ô dao động mạnh: `baseline/data-eval` 3/9→0/9→3/9; `skills-auto/data-eval` 1/9→3/9→3/9; `subagents/logs-eval` 0/10→2/10→0/10; `skills-auto/code-eval` 4/11→5/11→4/11 (ổn định nhất).
  - `skills_read=0/3` ở cả R1 và R2 mọi điều kiện; `subagent_calls=0` mọi lần subagents. Thứ hạng eval skills-auto tốt nhất cả 3 vòng dù không đọc skill — không giải thích được bằng cơ chế đọc-làm theo; có thể do hiệu ứng khung prompt (`SKILLS_NOTE`/thư mục `/skills/` đổi hành vi liệt kê tệp) hoặc ngẫu nhiên với n=3 tasks. Hạn chế: chỉ 3 mẫu/ô, chưa đủ ước lượng phương sai chuẩn; bước tiếp theo là 5+ lần lặp và kiểm định hoán vị (permutation test) trên điểm từng check.
  - Tái lập: `python -m lab.runner --condition {baseline,subagents,skills-auto} --tasks eval --results results-r1` (rồi `results-r2`); so sánh bằng `python -m lab.compare --results results-rX`.
- Ghi chú khác: `.env` đã chuẩn hóa từ `CUSTOM_*` sang `AZURE_OPENAI_*` (Option 1 cổng tương thích OpenAI) để khớp `model.py` mà không sửa code có sẵn; backup ở `.env.bak`. Hạn chế `run_task` tối thiểu: khi `agent.invoke` ném lỗi, `messages=[]` nên `trace.md` rỗng và `tool_calls=0` dù đã tốn hàng trăm nghìn token — số token vẫn đúng nhờ `UsageMetadataCallbackHandler`.
