import streamlit as st
import chess
import chess.svg
import base64
import requests
from chess_engine import ChessGame

def render_svg(svg):
    """Render SVG as a chess board in Streamlit."""
    b64 = base64.b64encode(svg.encode('utf-8')).decode()
    html = f'<img src="data:image/svg+xml;base64,{b64}" style="width: 400px; border:2px solid #444; border-radius:10px;"/>'
    st.markdown(html, unsafe_allow_html=True)

def lichess_best_move(fen):
    """Query the Lichess Cloud Evaluation API for the best move in the given FEN position."""
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

st.set_page_config(page_title="Interactive Chess App", layout="centered")
st.title("♟️ Interactive Chess App")

with st.expander("How to Play", expanded=False):
    st.markdown(
        "Select your move from the dropdown or enter it manually (UCI format, e.g., e2e4). "
        "You can also get the best move suggestion from Lichess Cloud Stockfish engine by clicking the button."
    )

if "game" not in st.session_state:
    st.session_state.game = ChessGame()
if "history" not in st.session_state:
    st.session_state.history = []
if "move_explanation" not in st.session_state:
    st.session_state.move_explanation = ""

game = st.session_state.game

col1, col2 = st.columns([2, 1])

with col1:
    lastmove = chess.Move.from_uci(st.session_state.history[-1]) if st.session_state.history else None
    svg_board = chess.svg.board(game.board, size=400, lastmove=lastmove)
    render_svg(svg_board)

    st.write("#### Move Selection")
    legal_moves = [move.uci() for move in game.board.legal_moves]
    move_input = st.selectbox("Select your move", [""] + legal_moves)
    manual_move = st.text_input("Or enter move (UCI):", "")

    move_submitted = st.button("Make Move")

    if move_submitted:
        selected_move = manual_move.strip() if manual_move.strip() else move_input
        if selected_move and selected_move in legal_moves:
            success, explanation = game.push_move(selected_move)
            if success:
                st.session_state.history.append(selected_move)
                st.session_state.move_explanation = explanation
            else:
                st.warning(explanation)
        else:
            st.warning("Please select or enter a valid legal move.")

    fen = game.board.fen()
    if st.button("Get Best Move (Lichess AI)"):
        with st.spinner("Querying Lichess Cloud Engine..."):
            best_move, eval_cp = lichess_best_move(fen)
        if best_move:
            eval_text = f"Evaluation: {'+' if eval_cp and eval_cp >= 0 else ''}{eval_cp} cp" if eval_cp is not None else ""
            st.success(f"Lichess Cloud recommends: **{best_move}** {eval_text}")
        else:
            st.error("Could not retrieve cloud analysis.")

    if game.is_game_over():
        st.markdown(f"### Game Over: {game.get_result()}")

with col2:
    mode = st.radio("Mode", ["Human vs Human", "Human vs AI"])
    if mode == "Human vs AI" and not game.is_game_over() and len(legal_moves) > 0:
        if st.button("AI Move"):
            move, explanation = game.ai_move(level='random')
            st.session_state.history.append(move)
            st.session_state.move_explanation = explanation
    if st.button("Restart Game"):
        st.session_state.game = ChessGame()
        st.session_state.history = []
        st.session_state.move_explanation = ""

    st.write("#### Last Move Explanation:")
    st.info(st.session_state.move_explanation)

# Sidebar move list, formatted for PGN-style display
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
