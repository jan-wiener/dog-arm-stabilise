import random
ranks = {"A": 11,
         "Q": 10,
         "K": 10,
         "J": 9}

ranks.update({str(i): i for i in range(2,11)})

last_id = -1
players_global = []

class Player():
    def __init__(self, name):
        global last_id
        self.name = name
        self.id, last_id = last_id + 1, last_id + 1
        self.cards = []
        players_global.append(self)

dealer = Player("Dealer")

class Game():
    def __init__(self, player_list: list = players_global):
        self.deck = self.new_deck()
        self.players = player_list
        #self.dealer = Player("Dealer")

    @staticmethod
    def new_deck():
        deck = list(ranks.keys()) * 4
        random.shuffle(deck)
        return deck
    
    def hit(self, player, amount):
        given = []
        for i in range(amount):
            given.append(self.deck.pop(0))
            player.cards.append(given[-1])
        return given
    
    @staticmethod
    def eval_cards(player):
        s = 0
        hand = {i: 0 for i in ranks}
        for card in player.cards:
            hand[card] = hand[card] + 1
            s += ranks[card]
        if s <= 21:
            return s
        while hand["A"] > 1:
            s-=10
            hand["A"] = hand["A"] - 1
        return s
   
    def print_cards(self, reveal: bool = False):
        for i in self.players:
            if i.id != 0 or reveal:
                print(f"{i.name}: {i.cards} - Value: {self.eval_cards(i)}")
            else:
                print(f"{i.name}: {i.cards[0]}")


    def start(self):
        for i in range(2):
            for player in self.players:
                self.hit(player,1)
        self.print_cards(False)
        self.interact_loop()


    def interact_loop(self):
        while True:
            player = self.players[1]
            inp = input("h/s: ")
            if inp == "h":
                given = self.hit(player,1)
                print(player.cards)
            elif inp == "s":
                break
        self.print_cards(True)
        
        






p1 = Player("Adam")
game = Game()
game.start()

game.print_cards()


print(game.eval_cards(p1))



