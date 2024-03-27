from OcrWordFeudBoard import Square, OcrWordfeudBoard, WordFeudBoard
import sys
import random
import scrabbler as sc
import os
import shutil
import time

def poll_updated_screenshot(image_path):
    # check if there is a new file in the directory ~/Downloads with name like IMG_*.jpeg
    download_dir = os.path.expanduser("~/Downloads")
    for filename in os.listdir(download_dir):
        if filename.startswith("IMG_") and filename.endswith(".jpeg"):
            # move the file to image_path
            new_file_path = os.path.join(download_dir, filename)
            shutil.move(new_file_path, image_path)
            print(f"\rFound new screenshot: {filename}")
            return True
    return False

def find_move(image_path, ocr, wf, game, tile_bag):
    rack = ocr.get_rack_letters(image_path)
    [tile_bag.remove(letter) for letter in rack]
    ocr.read_board_letters(image_path)
    for i in range(15):
        for j in range(15):
            if ocr.read_square(i,j) != '  ':
                wf.board[i][j].letter = ocr.read_square(i,j).strip()

    _ , placement = wf.all_board_words(wf.board)
    for i in placement:
        game.play(i[0], i[1], i[2])

    game.show()
    rack = "".join(rack)
    print(f"rack = {rack}")

    options = game.find_best_moves(rack)
    op_max = len(options)-1
    if options:
        user_input = input(f"Enter option to play from 0 to {op_max}:")
        if user_input.isdigit() and int(user_input) in range(op_max):
            move = options[int(user_input)]
            print(f"move = {move[0]} {move[1]} {move[2]}")
            game.play(move[0], move[1], move[2])
            game.show()

if __name__ == "__main__":
    tile_bag = ["A"] * 9 + ["B"] * 2 + ["C"] * 2 + ["D"] * 4 + ["E"] * 12 + ["F"] * 2 + ["G"] * 3 + \
                ["H"] * 2 + ["I"] * 9 + ["J"] * 1 + ["K"] * 1 + ["L"] * 4 + ["M"] * 2 + ["N"] * 6 + \
                ["O"] * 8 + ["P"] * 2 + ["Q"] * 1 + ["R"] * 6 + ["S"] * 4 + ["T"] * 6 + ["U"] * 4 + \
                ["V"] * 2 + ["W"] * 2 + ["X"] * 1 + ["Y"] * 2 + ["Z"] * 1 + ["%"] * 2


    image_path = "images/WordFeudScreenshot1.jpeg"
    ocr = OcrWordfeudBoard(image_path)
    wf = WordFeudBoard()
    game = sc.Game(board="wordfeud")
    i = 0
    while True:
        while poll_updated_screenshot(image_path)==False:
            i += 1
            print(f"\rwaiting for updated screenshot {i}", end="")
            time.sleep(10)
        find_move(image_path, ocr, wf, game, tile_bag)
        game.board.reset_board("wordfeud")


# TODO For each choice of move figure out the best move for the opponent based
# on the current board state and the opponent's rack.
# Play the next hand and see which one scores higher
# See if the board can be reset to the original state after each move
# If not, then the board should be copied before each move
# If the board can be reset, then the board should be reset after each move

# TODO Fix the scoring
