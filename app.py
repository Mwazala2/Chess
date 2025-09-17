import streamlit as st
import chess
import chess.svg
import base64
import requests
import openai
from chess_engine import ChessGame

def render_svg(svg):
    b64 = base64.b64encode(svg.encode('utf-8')).decode()
    html = f'<img src="data:image/svg+xml;base64,{b64}" style="width: 400px; border:2px solid #444; border-radius:10px;"/>'
    st.markdown(html, unsafe_allow_html=True)

def lichess_best_move(fen):
    api_key = st.secrets["lichess_api_key"]
    url = "https://lichess.org/api/cloud-eval"
    params = {"fen": fen, "multiPv": 1}
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["pvs"][0]["moves"].split()[0], data["pvs"][0].get("cp", None)
    else:
        return None, None

def openai_commentary(fen):
    client = openai.OpenAI(api_key=st.secrets["openai_api_key"])
    prompt = (
        f"This is a chess position in FEN notation: '{fen}'. "
        "Please provide a brief analysis and suggest a strong move for the side to move. "
        "Explain the reasoning in simple terms for a chess learner."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use this model unless you have gpt-4 access!
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI error: {e}"

st.set_page_config(page_title="Interactive Chess App", layout="centered")
st.title("♟️ Interactive Chess App")

with st.expander("How to Play", expanded=False):
    st.markdown(
        "Select your move from the dropdown or enter it manually (UCI format: e2e4, g1f3, e7e8q for promotion)."
        "\nOnly legal moves are accepted. Commentary and best move suggestions are available."
    )

if "game" not in st.session_state:
    st.session_state.game = ChessGame()
if "history" not in st.session_state:
    st.session_state.history = []
if "move_explanation" not in st.session_state:
    st.session_state.move_explanation = ""
if "ai_difficulty" not in st.session_state:
    st.session_state.ai_difficulty = "Easy"
if "ai_engine_source" not in st.session_state:
    st.session_state.ai_engine_source = "Local Stockfish"

game = st.session_state.game

st.sidebar.markdown("## AI Configuration")
ai_difficulty = st.sidebar.selectbox("AI Difficulty", ["Easy", "Intermediate", "Hard"], index=["Easy","Intermediate","Hard"].index(st.session_state.ai_difficulty))
st.session_state.ai_difficulty = ai_difficulty

if ai_difficulty == "Hard":
    ai_engine_source = st.sidebar.selectbox("Engine Source", ["Local Stockfish", "Lichess Cloud"], index=["Local Stockfish","Lichess Cloud"].index(st.session_state.ai_engine_source))
    st.session_state.ai_engine_source = ai_engine_source
else:
    st.session_state.ai_engine_source = "Local Stockfish"

col1, col2 = st.columns([2, 1])

with col1:
    lastmove = chess.Move.from_uci(st.session_state.history[-1]) if st.session_state.history else None
    svg_board = chess.svg.board(game.board, size=400, lastmove=lastmove)
    render_svg(svg_board)

    st.write("#### Move Selection")
    legal_moves = [move.uci() for move in game.board.legal_moves]
    move_input = st.selectbox("Select your move", [""] + legal_moves)
    st.write("Enter moves in UCI format (e.g., e2e4, g1f3, e7e8q for promotion)")
    manual_move = st.text_input("Or enter move (UCI):", "")

    def is_valid_uci(move):
        return move in legal_moves

    move_submitted = st.button("Make Move")
    if move_submitted:
        selected_move = manual_move.strip() if manual_move.strip() else move_input
        if selected_move and is_valid_uci(selected_move):
            success, explanation = game.push_move(selected_move)
            if success:
                st.session_state.history.append(selected_move)
                st.session_state.move_explanation = explanation
            else:
                st.warning(explanation)
        else:
            st.warning("❌ Invalid or illegal move. Please use UCI format and only play legal moves.")

    fen = game.board.fen()
    if st.button("Get Best Move (Lichess AI)"):
        with st.spinner("Querying Lichess Cloud Engine..."):
            best_move, eval_cp = lichess_best_move(fen)
        if best_move:
            eval_text = f"Evaluation: {'+' if eval_cp and eval_cp >= 0 else ''}{eval_cp} cp" if eval_cp is not None else ""
            st.success(f"Lichess Cloud recommends: **{best_move}** {eval_text}")
        else:
            st.error("Could not retrieve cloud analysis.")

    if st.button("Get OpenAI Commentary on Position"):
        with st.spinner("Querying OpenAI..."):
            commentary = openai_commentary(fen)
        st.info(commentary)

    if game.is_game_over():
        st.markdown(f"### Game Over: {game.get_result()}")

with col2:
    mode = st.radio("Mode", ["Human vs Human", "Human vs AI"])
    if mode == "Human vs AI" and not game.is_game_over() and len(legal_moves) > 0:
        if st.button("AI Move"):
            level = st.session_state.ai_difficulty.lower()
            engine_source = "local" if st.session_state.ai_engine_source == "Local Stockfish" else "lichess"
            if level == "hard" and engine_source == "lichess":
                with st.spinner("Querying Lichess Cloud Engine..."):
                    best_move, eval_cp = lichess_best_move(game.board.fen())
                if best_move:
                    game.push_move(best_move)
                    st.session_state.history.append(best_move)
                    eval_text = f"Evaluation: {'+' if eval_cp and eval_cp >= 0 else ''}{eval_cp} cp" if eval_cp is not None else ""
                    st.session_state.move_explanation = f"Lichess Cloud recommends: {best_move}. {eval_text}"
                else:
                    st.error("Could not retrieve cloud analysis.")
            else:
                move, explanation = game.ai_move(level=level, engine_source=engine_source)
                if move:
                    st.session_state.history.append(move)
                    st.session_state.move_explanation = explanation
                else:
                    st.warning(explanation)

    if st.button("Restart Game"):
        st.session_state.game = ChessGame()
        st.session_state.history = []
        st.session_state.move_explanation = ""

    st.write("#### Last Move Explanation:")
    st.info(st.session_state.move_explanation)

st.sidebar.markdown("## Move History")
if st.session_state.history:
    move_list = ""
    for i in range(0, len(st.session_state.history), 2):
        move_no = i // 2 + 1
        white = st.session_state.history[i]
        black = st.session_state.history[i+1] if i+1 < len(st.session_state.history) else ""
        move_list += f"{move_no}. {white} {black}\n"
    st.sidebar.text_area("PGN", move_list, height=200)
else:
    st.sidebar.write("No moves yet.")
