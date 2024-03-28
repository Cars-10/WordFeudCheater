import os
import cv2
import numpy as np
import pytesseract
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import regexp as re
import random
import copy
import utilities.logger as logger
import utilities.errors as errors
class OcrWordfeudBoard():
    def __init__(self,image_path):
        self.board = [['  ' for _ in range(15)] for _ in range(15)]

    def update_square(self, x, y, value):
        self.board[x][y] = value

    def read_square(self, x, y):
        return self.board[x][y]

    def get_rack_letters(self, image_path):
        """
        Extracts the letters from the rack in the given image.

        Args:
            image_path (str): The path to the image containing the rack.

        Returns:
            list: A list of extracted letters from the rack.
        """
        logger.info("Extracting rack letters...")
        cropped_rack = self.open_and_crop_image(image_path, 15, 1700, 930, 120)
        #cv2.imwrite('images/cropped_rack.png', cropped_rack)

        letters = []
        square_size = cropped_rack.shape[1] // 7
        padding = 20

        for i in range(7):
            top_left_y = padding
            bottom_right_y = square_size - padding
            top_left_x = i * square_size + padding
            bottom_right_x = (i + 1) * square_size - padding * 2
            square = cropped_rack[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
            #print(f"top_left_y: {top_left_y}, bottom_right_y: {bottom_right_y}, top_left_x: {top_left_x}, bottom_right_x: {bottom_right_x}")
            letter = self.ocr_tile(square,threshold=2, save_image=False, comments="")
            letters.append(letter)
        return letters

    def ocr_tile(self, tile, threshold=5, save_image=False, comments=""):
        """
        Perform OCR (Optical Character Recognition) on a given tile image.

        Args:
            tile: A numpy array representing the tile image.

        Returns:
            The recognized letter from the tile image, or '+' if no letter is recognized.
        """
        image = Image.fromarray(tile)
        grayscale_image = image.convert("L")
        binary_image = grayscale_image.point(lambda x: 255 if x > threshold else 0, mode='1')
        letter = pytesseract.image_to_string(binary_image, config='--psm 10 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ "')
        if letter:
            letter = letter[0]
        else:
            letter = '%'

        if save_image:
            binary_image.save('images/tmp/ocr_tile_'+letter+comments+'.png')
        if comments:
            print(f"OCR:{letter} {comments} ")

        return letter

    def classify_dominant_color(self, image, threshold=50):
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:5, :5]
        # Define HSV ranges for different colors
        color_ranges = {
            'white': (np.array([0, 0, 200]), np.array([180, 55, 255])),
            'yellow': (np.array([22, 30, 170]), np.array([45, 150, 255]))
        }
           # 'green': (np.array([35, 50, 50]), np.array([85, 255, 255])),
           # 'blue': (np.array([100, 50, 50]), np.array([140, 255, 255])),
           # 'red2': (np.array([160, 50, 50]), np.array([180, 255, 255])),
           # 'orange': (np.array([10, 100, 20]), np.array([25, 255, 255])),
           # 'dark gray': (np.array([30, 30, 40]), np.array([60, 70, 60]))

        max_percentage = 0
        dominant_color = False

        for color, (lower, upper) in color_ranges.items():
            # Create a mask for the current color range
            mask = cv2.inRange(hsv, lower, upper)

            # Calculate the percentage of pixels in the current color range
            percentage = (np.sum(mask > 0) / mask.size) * 100

            # Update dominant color if current percentage is higher
            if percentage > max_percentage and percentage > threshold:
                max_percentage = percentage
                dominant_color = color
                #print(f"Found {color} in image.", end="")

            #if not dominant_color:
            #    print("White/Yellow not found in image.")

        return dominant_color

    def segment_board_into_squares(self, image):
            """
            Segments the given image of a Scrabble board into individual squares.

            Args:
                image (numpy.ndarray): The image of the Scrabble board.

            Returns:
                list: A list of numpy arrays, each representing an individual square on the board.
            """
            squares = []
            square_size = image.shape[0] // 15  # Assuming a standard 15x15 Scrabble board
            padding = 8
            for i in range(15):
                for j in range(15):
                    top_left_y = i * square_size + padding
                    bottom_right_y = (i + 1) * square_size - padding
                    top_left_x = j * square_size + padding
                    bottom_right_x = (j + 1) * square_size - padding*2 - 2
                    square = image[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
                    #print(f"top_left_y: {top_left_y}, bottom_right_y: {bottom_right_y}, top_left_x: {top_left_x}, bottom_right_x: {bottom_right_x}")
                    squares.append(square)
            return squares

    def read_board(self, squares):
        """
        Reads the WordFeud board and returns the letters on the board as a string.

        Args:
            squares (list): A list of image squares representing the WordFeud board.
            static_tiles (list): A list of image tiles representing the static tiles on the board.

        Returns:
            str: A string containing the letters on the board.

        """
        board_letters = ""
        # check if square is a static tile
        count = 0
        for square in squares:
            row = count // 15
            column = count % 15
            #print(f"Reading square {row},{column}")
            dominant_color = self.classify_dominant_color(square)
            #cv2.imwrite('images/tmp/ocr_square_'+str(row)+','+str(column)+'.png', square)

            if dominant_color == 'white' or dominant_color == 'yellow':
                letter = self.ocr_tile(square, save_image=False, comments="")
                self.update_square(row, column, letter)
                board_letters = board_letters + letter + " "
            count += 1
        return board_letters

    def open_and_crop_image(self, image_path, x, y, w, h):
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        # Resize image to always be 960 × 2079 pixels
        # This hack should allow screenshots from other phones to be used
        img = cv2.resize(img, (960, 2079))
        # convert 16-bit to 8-bit
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        return img[y:y+h, x:x+w]

    # create function to save board to file
    def save_board_file(self, file_path):
        with open(file_path, 'w') as file:
            for row in self.board:
                file.write(','.join(row) + '\n')
        print(f"Board saved to {file_path}.")


    def read_board_letters(self, image_path):
        """
        Reads the letters on the WordFeud board from either a saved file or an image.

        Args:
            image_path (str): The path to the image of the WordFeud board.

        Returns:
            list: A list of letters representing the WordFeud board.

        """
        logger.info("Reading WF Screenshot...")

        # Perform the necessary operations to read the board from the image
        cropped_board = self.open_and_crop_image(image_path, 0, 500, 960, 960)
        #cv2.imwrite('images/cropped_board.png', cropped_board)
        squares = self.segment_board_into_squares(cropped_board)
        board_letters = self.read_board(squares)
        # Uncomment to save the board to a file for quicker debugging avoiding OCR
        #self.save_board_file(saved_board_path)
        return board_letters



class Square:
    def __init__(self, letter=None, modifier="Normal"):
        self.letter = letter
        self.modifier = modifier
        self.visible = True

    def __str__(self):
        if not self.visible:
            return ""
        if not self.letter:
            return "_"
        else:
            return self.letter


class WordFeudBoard:
    def __init__(self):
        self.board = []
        # variables to encode best word on a given turn
        self.word_rack = []

        # populate self.board with 15 rows of 15 Squares() columns
        self.board = [[Square() for _ in range(15)] for _ in range(15)]


    def all_board_words(self, board):
        """
        Retrieves all the words present on the game board.

        Args:
            board (list): A 2D list representing the game board.

        Returns:
            list: A list of words found on the game board.
        """
        board_words = []
        placement = []
        board_words.extend(self.check_regular_board(board, placement))
        board_words.extend(self.check_transposed_board(board, placement))
        return board_words, placement

    def check_regular_board(self, board, placement):
        board_words = []
        for row in range(15):
            temp_word = ""
            for col in range(16):
                if col == 15:
                    letter = "" # padding so that end of word is reached
                else:
                    letter = board[row][col].letter

                if letter:
                    temp_word += letter
                    #print(f"H temp_word: {temp_word}")
                else:
                    if len(temp_word) > 1:
                        board_words.append(temp_word)
                        placement.append([(row, col-len(temp_word)), temp_word, "across"])
                    temp_word = ""
        return board_words

    def check_transposed_board(self, board, placement):
        board_words = []
        for col in range(15):
            temp_word = ""
            for row in range(16):
                if row == 15:
                    letter = "" # padding so that end of word is reached
                else:
                    letter = board[row][col].letter

                if letter:
                    temp_word += letter
                    #print(f"V temp_word: {temp_word}")
                else:
                    if len(temp_word) > 1:
                        placement.append([(row-len(temp_word), col), temp_word, "down"])
                        board_words.append(temp_word)
                    temp_word = ""
        return board_words



