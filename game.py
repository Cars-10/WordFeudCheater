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

def remaining_letters(game, played_letters):
    # A list to collect keys to remove after iteration
    keys_to_remove = []
    formatted_list = []
    tiles_left = 0
    # Reducing the tile count based on played letters
    for letter in played_letters:
        if letter in game.tiles_count:
            game.tiles_count[letter] -= 1
            # Check if the count is 0 to mark for removal
            if game.tiles_count[letter] == 0:
                keys_to_remove.append(letter)

    # Removing entries with 0 count
    for key in keys_to_remove:
        del game.tiles_count[key]

    sorted_tile_count = dict(sorted(game.tiles_count.items()))
    # Formatting and printing the sorted tile counts
    for letter, count in sorted_tile_count.items():
        formatted_list.append(f"{letter}={count} ")
        tiles_left += count

    return tiles_left, ''.join(formatted_list)


def find_move(image_path, ocr, wf, game):
    rack = ocr.get_rack_letters(image_path)
    played_letters = ocr.read_board_letters(image_path)
    # Transfer OCR'd board to WordFeudBoard
    for i in range(15):
        for j in range(15):
            if ocr.read_square(i,j) != '  ':
                wf.board[i][j].letter = ocr.read_square(i,j).strip()

    _ , placement = wf.all_board_words(wf.board)
    for i in placement:
        game.play(i[0], i[1], i[2])

    #game.board._print_special_tiles()
    game.show()
    rack = ''.join(rack)
    print(f"Rack: {rack}")
    count, letter = remaining_letters(game, played_letters)
    print(f"Tiles Left {count}: {letter}")

    options = game.find_best_moves(rack)
    op_max = len(options)-1
    print("\nPossible Moves:")
    if options:
        user_input = input(f"\nEnter option to play from 0-{op_max}: ")
        if user_input.isdigit() and int(user_input) in range(op_max):
            move = str(options[int(user_input)]).split('|')

            print(f"{move[0]}, {move[1]}, {move[2]}")
            game.play(str(move[0]), move[1], move[2])
            game.show()

if __name__ == "__main__":
    image_path = "images/WordFeudScreenshot.jpeg"
    ocr = OcrWordfeudBoard(image_path)
    wf = WordFeudBoard()
    game = sc.Game(board="wordfeud")

    i = 0
    while True:
        while poll_updated_screenshot(image_path)==False:
            i += 1
            print(f"\rWaiting 10 seconds for updated screenshot {i}", end="")
            time.sleep(10)
        find_move(image_path, ocr, wf, game)
        game.board.reset_board("wordfeud")
