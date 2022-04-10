import string

# chess board parameters
TILES_PER_SIDE = 8
TILE_LENGTH = 100  # pixels
DARK_COLOR = "#1b262c"
LIGHT_COLOR = "#0f4c75"

# square names with all their belonging coordinates
squares_and_coordinates = {}
for X in range(TILES_PER_SIDE):
    for Y in range(TILES_PER_SIDE):
        tile_id = string.ascii_lowercase[:TILES_PER_SIDE][X] + string.digits[TILES_PER_SIDE:0:-1][Y]
        tile_coordinates = [(x, y) for x in range(X * TILE_LENGTH, (X + 1) * TILE_LENGTH) for y in range(Y * TILE_LENGTH, (Y + 1) * TILE_LENGTH)]
        squares_and_coordinates[tile_id] = tile_coordinates

# all squares and their belonging central coordinates
square_centres = {}
for square in squares_and_coordinates:
    coordinates = (squares_and_coordinates[square][0][0] + TILE_LENGTH // 2, squares_and_coordinates[square][0][1] + TILE_LENGTH // 2)
    square_centres[square] = coordinates


# classic initial piece positions
pieces_and_positions = {
    "white_pawn_1": "a2",
    "white_pawn_2": "b2",
    "white_pawn_3": "c2",
    "white_pawn_4": "d2",
    "white_pawn_5": "e2",
    "white_pawn_6": "f2",
    "white_pawn_7": "g2",
    "white_pawn_8": "h2",
    "white_rook_1": "a1",
    "white_knight_1": "b1",
    "white_bishop_1": "c1",
    "white_queen_1": "d1",
    "white_king_1": "e1",
    "white_bishop_2": "f1",
    "white_knight_2": "g1",
    "white_rook_2": "h1",
    "black_pawn_1": "a7",
    "black_pawn_2": "b7",
    "black_pawn_3": "c7",
    "black_pawn_4": "d7",
    "black_pawn_5": "e7",
    "black_pawn_6": "f7",
    "black_pawn_7": "g7",
    "black_pawn_8": "h7",
    "black_rook_1": "a8",
    "black_knight_1": "b8",
    "black_bishop_1": "c8",
    "black_queen_1": "d8",
    "black_king_1": "e8",
    "black_bishop_2": "f8",
    "black_knight_2": "g8",
    "black_rook_2": "h8",
}

# starting piece positions for original setup reference
starting_positions = pieces_and_positions.copy()

# representing tile lettering as numbers for move validating calculations, and vice versa
numeric_equivalent = {letter: number for number, letter in enumerate(string.ascii_lowercase[:TILES_PER_SIDE], start=1)}
lettered_equivalent = {number: letter for number, letter in enumerate(string.ascii_lowercase[:TILES_PER_SIDE], start=1)}
