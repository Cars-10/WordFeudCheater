import os
import cv2
import numpy as np
import pytesseract
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import regex as re
import random
import copy
import utilities.logger as logger
import utilities.errors as errors


class OcrWordfeudBoard():
    def __init__(self,image_path):
        self.board = [['  ' for i in range(15)] for j in range(15)]

    def update_square(self, x, y, value):
        self.board[x][y] = value

    def read_square(self, x, y):
        return self.board[x][y]

    def display_board(self):
        for row in self.board:
            print('  '.join(row))


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
        cv2.imwrite('images/cropped_rack.png', cropped_rack)

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
            letters.append(self.ocr_tile(square))
        return letters

    def ocr_tile(self, tile):
        """
        Perform OCR (Optical Character Recognition) on a given tile image.

        Args:
            tile: A numpy array representing the tile image.

        Returns:
            The recognized letter from the tile image, or '+' if no letter is recognized.
        """

        image = Image.fromarray(tile)
        grayscale_image = image.convert("L")
        threshold = 50
        binary_image = grayscale_image.point(lambda x: 255 if x > threshold else 0, mode='1')
        letter = pytesseract.image_to_string(binary_image, config='--psm 10 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ "')
        if letter:
            letter = letter[0]
        else:
            letter = '%'
        #binary_image.save('images/tmp/ocr_tile_'+letter+'.png')
        return letter

    def classify_dominant_color(self, image, threshold=50):
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # Define HSV ranges for different colors
        color_ranges = {
           # 'green': (np.array([35, 50, 50]), np.array([85, 255, 255])),
           # 'blue': (np.array([100, 50, 50]), np.array([140, 255, 255])),
            'yellow': (np.array([22, 30, 170]), np.array([45, 150, 255])),
           # 'red2': (np.array([160, 50, 50]), np.array([180, 255, 255])),
           # 'orange': (np.array([10, 100, 20]), np.array([25, 255, 255])),
            'white': (np.array([0, 0, 200]), np.array([180, 55, 255])),
           # 'dark gray': (np.array([30, 30, 40]), np.array([60, 70, 60]))
        }

        max_percentage = 0
        dominant_color = None

        for color, (lower, upper) in color_ranges.items():
            # Create a mask for the current color range
            mask = cv2.inRange(hsv, lower, upper)

            # Calculate the percentage of pixels in the current color range
            percentage = (np.sum(mask > 0) / mask.size) * 100

            # Update dominant color if current percentage is higher
            if percentage > max_percentage and percentage > threshold:
                max_percentage = percentage
                dominant_color = color

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
                    bottom_right_x = (j + 1) * square_size - padding*2
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
            dominant_color = self.classify_dominant_color(square)

            if dominant_color == 'white' or dominant_color == 'yellow':
                #print(f"The image {row},{column} is mostly {dominant_color}.")
                #cv2.imwrite('images/tmp/ocr_square_'+str(row)+','+str(column)+'.png', square)
                letter = self.ocr_tile(square)
                self.update_square(row, column, letter + " ")
                board_letters = board_letters + letter
            count += 1
        return board_letters

    def open_and_crop_image(self, image_path, x, y, w, h):
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        # convert 16-bit to 8-bit
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        return img[y:y+h, x:x+w]

    # create function to save board to file
    def save_board_file(self, file_path):
        with open(file_path, 'w') as file:
            for row in self.board:
                file.write(','.join(row) + '\n')
        print(f"Board saved to {file_path}.")

    def read_board_file(self, file_path):
            """
            Read the board from the given file and update the current board.

            Parameters:
            - file_path (str): The path to the file containing the board.

            Returns:
            - list: The updated board as a list of lists.

            """
            with open(file_path, 'r') as file:
                lines = file.readlines()
                self.board = [line.strip("\n").split(",") for line in lines]
                # replace all occurences of special_squares = ['DL', 'DW', 'TL', 'TW'] with '  ' in self.board
                for i in range(len(self.board)):
                    for j in range(len(self.board[i])):
                        if self.board[i][j] in ['DL', 'DW', 'TL', 'TW']:
                            self.board[i][j] = '  '

            print(f"Board read from {file_path}.")
            return self.board

    def read_board_letters(self, image_path):
        """
        Reads the letters on the WordFeud board from either a saved file or an image.

        Args:
            image_path (str): The path to the image of the WordFeud board.

        Returns:
            list: A list of letters representing the WordFeud board.

        """
        logger.info("Reading WF Screenshot...")

        saved_board_path = "games/WordFeudBoard.txt"

        # If board file exists, read the board from the file
        # to avoid the OCR process
        if os.path.isfile(saved_board_path):
            board_letters = self.read_board_file(saved_board_path)
        else:
            # Perform the necessary operations to read the board from the image
            cropped_board = self.open_and_crop_image(image_path, 0, 500, 960, 960)
            cv2.imwrite('images/cropped_board.png', cropped_board)
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
        # check regular board
        for row in range(15):
            temp_word = ""
            for col in range(15):
                letter = board[row][col].letter
                if letter:
                    temp_word += letter
                    #print(f"temp_word = {temp_word}")
                else:
                    if len(temp_word) > 1:
                        #print(f'game.play(({row}, {col-len(temp_word)}), "{temp_word}", "across")')
                        board_words.append(temp_word)
                        placement.append([(row, col-len(temp_word)), temp_word, "across" ])
                        #print(f"Final temp_word = {temp_word}")
                    temp_word = ""

        # check transposed board
        for col in range(15):
            temp_word = ""
            for row in range(15):
                letter = board[row][col].letter
                if letter:
                    # sums up letters till theres a space
                    temp_word += letter
                    #print(f"temp_word = {temp_word}")
                else:
                    if len(temp_word) > 1:
                        #print(f'game.play(({row-len(temp_word)},{col}), "{temp_word}", "down")')
                        placement.append([(row-len(temp_word), col), temp_word, "down"])
                        board_words.append(temp_word)
                        #print(f"Final temp_word = {temp_word}")
                    temp_word = ""
        #print(f"board_words = {board_words}")
        return board_words, placement


