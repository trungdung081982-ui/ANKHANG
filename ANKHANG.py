else:
        st.title("📝 LUYỆN THI VÀO 10")
        
        # Nút tạo đề mới
        if st.button("🆕 LÀM ĐỀ THI MỚI (40 CÂU)", type="primary"):
            st.session_state.exam = ExamGenerator().generate_all()
            st.session_state.sub = False
            # Xóa các câu trả lời cũ trong session_state
            for key in list(st.session_state.keys()):
                if key.startswith("q"): del st.session_state[key]
            st.rerun()

        if st.session_state.exam:
            # --- PHẦN HIỂN THỊ ĐIỂM SỐ PHÍA TRÊN ---
            if st.session_state.sub:
                # Tính toán lại kết quả để hiển thị
                corr = sum(1 for i, q in enumerate(st.session_state.exam) if st.session_state.get(f"q{i}") == q['answer'])
                score = round((corr/40)*10, 2)
                
                # Tạo khung hiển thị điểm nổi bật phía trên bên phải
                res_col1, res_col2 = st.columns([2, 1])
                with res_col2:
                    st.markdown("""
                        <style>
                        .score-box {
                            background-color: #f0f2f6;
                            padding: 20px;
                            border-radius: 10px;
                            border-left: 5px solid #ff4b4b;
                            text-align: center;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    with st.container():
                        st.markdown('<div class="score-box">', unsafe_allow_html=True)
                        st.subheader("📊 KẾT QUẢ")
                        c1, c2 = st.columns(2)
                        c1.metric("Đúng", f"{corr}/40")
                        c2.metric("Điểm số", f"{score}")
                        st.markdown('</div>', unsafe_allow_html=True)
                st.divider()

            # --- HIỂN THỊ DANH SÁCH CÂU HỎI ---
            for i, q in enumerate(st.session_state.exam):
                st.write(f"**Câu {i+1}:** {q['question']}")
                if q['image']: 
                    st.image(f"data:image/png;base64,{q['image']}")
                
                # Lấy giá trị đã chọn hoặc mặc định là None
                current_choice = st.session_state.get(f"q{i}")
                ans = st.radio("Chọn:", q['options'], key=f"q{i}", disabled=st.session_state.sub)
                
                if st.session_state.sub:
                    if ans == q['answer']: 
                        st.success(f"Đúng ✅ (Đáp án: {q['answer']})")
                    else:
                        st.error(f"Sai ❌. Đáp án đúng: {q['answer']}")
                        st.info(f"💡 {q['hint']}")
                st.divider()

            # --- NÚT NỘP BÀI ---
            if not st.session_state.sub:
                if st.button("🎯 NỘP BÀI", type="primary", use_container_width=True):
                    # Tính điểm
                    corr = sum(1 for i, q in enumerate(st.session_state.exam) if st.session_state.get(f"q{i}") == q['answer'])
                    score = round((corr/40)*10, 2)
                    
                    # Lưu vào database
                    conn = sqlite3.connect('exam_db.sqlite')
                    conn.execute("INSERT INTO results (username, score, correct_count, wrong_count) VALUES (?,?,?,?)", 
                                (st.session_state.user, score, corr, 40-corr))
                    conn.commit()
                    conn.close()
                    
                    st.session_state.sub = True
                    st.balloons()
                    st.rerun()
