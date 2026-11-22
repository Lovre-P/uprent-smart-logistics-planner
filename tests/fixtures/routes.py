"""Fiksni redoslijedi radnji za neovisnu provjeru brojki iz zadatka."""


def ops(text):
    actions = {"P": "PICKUP", "D": "DELIVERY"}
    return [(actions[token[0]], token[2:]) for token in text.split()]


B_ALONE = ops("P:N08 P:N03 D:N08 P:N09 D:N09 P:N01 P:N05 D:N03 D:N05 P:N07 "
              "P:N02 D:N07 D:N01 D:N02 P:N06 D:N06 P:N10 D:N10 P:N04 D:N04")
STRICT_A = ops("P:N03 D:N03")
STRICT_B = ops("P:N05 P:N01 P:N02 D:N05 P:N07 D:N07 D:N01 D:N02 P:N06 "
               "D:N06 P:N10 D:N10 P:N04 P:N08 D:N08 P:N09 D:N09 D:N04")
BOUNDARY_A = ops("P:N04 D:N04")
BOUNDARY_B = ops("P:N05 P:N01 P:N02 D:N05 P:N07 D:N07 D:N01 D:N02 P:N06 "
                 "D:N06 P:N10 D:N10 P:N08 P:N03 D:N08 P:N09 D:N09 D:N03")
