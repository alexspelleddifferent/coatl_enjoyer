import requests
import json
import re
import time
import publisher
from PIL import Image, ImageDraw, ImageFont

def event_finder():
# goes to mtgo website and finds the events at time of running the program, returns a list of urls 
    url2='https://www.mtgo.com/en/mtgo/decklists'
    event_webpg=requests.get(url2)

    list_start=event_webpg.text.find('<ul class="decklists-list">')+28
    list_end=(event_webpg.text.find('<footer class="site-footer" id="footer">')-44)

    event_string=event_webpg.text[list_start:list_end]

    event_list=re.findall('/en/mtgo/decklist.*\d"', event_string)
    return event_list

def event_comparer(event_list_new):
# compare a list of events to the saved list and returns a list that has the difference of the the last events from the checked events
    historic_lists=open("event_list.txt","r")
    last_events=historic_lists.read()
    historic_lists.close()

    last_events=last_events.replace('"','" ').split()
    new_events=list(set(event_list_new)-set(last_events))

    event_saver(event_list_new)
    logger(new_events)
    return new_events

def event_saver(event_list):
# takes an events list and saves it to a text file for future use
    historic_lists=open("event_list.txt","w")
    historic_lists.writelines(event_list)
    historic_lists.close()

def event_parser(event_list, card_of_interest):
# parses through an event, grabs decklists, builds new decklists, checks presence of card of interest, 
# returns a list of decks with the desired card
    decks_with_card=[]
    for event in event_list:
        list_of_decks, event_name=decks_grabber(event)
        for deck in list_of_decks:
            current_deck=deck_constructor(deck, event_name)
            if card_checker(card_of_interest, current_deck):
                decks_with_card.append(current_deck)
    return decks_with_card

def decks_grabber(event):
# grabs an event from the website and checks if it is a modern or legacy event. 
# if it is, it grabs the decks from the event and returns them and the name of the event     
    decks_list={}
    event_name="Not relevant"
    if "modern" in event or "legacy" in event:
        url='https://www.mtgo.com'+event[:-1]
        resp=requests.get(url)
        event_name=' '.join(event.split('/')[4].split('-')[:-3])
        decks="{"+resp.text[resp.text.find('"decks":'):(resp.text.find('window.MTGO.decklists.roundNames')-6)]
        finishes_dict=json.loads(decks)
        decks_list=finishes_dict['decks']
    return decks_list, event_name

def deck_constructor(deck, event_name):
# takes a raw decklist dictionary and the name of the event and builds a decklist and returns it
    current_player=deck["player"]
    current_decklist={'Player':current_player, 'Event':event_name}
    for j in range(len(deck['deck'])):
        if deck['deck'][j]['SB']==True:
            card_category='Sideboard'
        else:
            card_category='Main Deck'
        current_decklist[card_category]={}
        for k in range(len(deck['deck'][j]['DECK_CARDS'])):
            card_quantity=deck['deck'][j]['DECK_CARDS'][k]['Quantity']
            try:
                card_type=deck['deck'][j]['DECK_CARDS'][k]['CARD_ATTRIBUTES']['Type']
            except:
                card_type='Split'
            card_name=deck['deck'][j]['DECK_CARDS'][k]['CARD_ATTRIBUTES']['NAME']
            current_decklist[card_category][card_name]=[card_type, card_quantity]
    return current_decklist

def card_checker(card_oi, decklist):
# takes a card, a decklist, and checks if the card is in the main deck of a decklist. returns true if it does, otherwise failse
    for card in decklist['Main Deck']:
        if card==card_oi:
            return True
    return False
        
def deck_transformer(decklist):
    organized_decks=[]
    for deck in decklist:
        current_decklist_created=\
            {'Player':deck['Player'], 'Event':deck['Event'],\
            'Main Deck':\
                {'Creatures':{}, 'Planeswalkers' :{}, 'Instants': {}, 'Sorceries':{}, 'Artifacts':{}, 'Enchantments':{}, 'Lands':{}},\
            'Sideboard': []}
        for card in deck['Main Deck']:
            try:
                if deck['Main Deck'][card][0]=='Creature':
                    current_decklist_created['Main Deck']['Creatures'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Planeswalker':
                    current_decklist_created['Main Deck']['Planeswalkers'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Instant':
                    current_decklist_created['Main Deck']['Instants'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Sorcery':
                    current_decklist_created['Main Deck']['Sorceries'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Artifact':
                    current_decklist_created['Main Deck']['Artifacts'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Enchantment':
                    current_decklist_created['Main Deck']['Enchantments'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Land':
                    current_decklist_created['Main Deck']['Lands'][card]=deck['Main Deck'][card][1]
            except:
                print("empty list")
        current_decklist_created['Sideboard']=deck['Sideboard']
        organized_decks.append(current_decklist_created)
    return organized_decks

def drawer(decklist):
    for deck in decklist:
        deck_name=(deck['Event']+deck['Player']).replace(" ","")
        deck_background=Image.open('deck_background.png')
        deck_image=ImageDraw.Draw(deck_background)
        big_font=ImageFont.truetype('OpenSans-Regular.ttf', 20)
        mid_font=ImageFont.truetype('OpenSans-Semibold.ttf', 13)
        small_font=ImageFont.truetype('OpenSans-Regular.ttf', 12)
        league_name=f'Event: {deck["Event"].title()}'
        deck_image.text((90,65), league_name, font=big_font, fill=(0, 0, 0))
        deck_image.text((570,65), ("Pilot: "+deck['Player']), font=big_font, fill=(0, 0, 0))
        
        # print("\n"+deck['Event'].upper()+"\n")
        # print(deck['Player'],"\n")
        # print("Main deck: ")
        row_count=1.7
        for category in deck['Main Deck']:
            if (deck['Main Deck'][category] and category!='Lands'):
                # print("\n"+category+":")
                deck_image.text((90,70+20*row_count), (category+":"), font=mid_font, fill=(0, 0, 0))
                row_count+=1
                for card in deck['Main Deck'][category]:
                    # print(deck['Main Deck'][category][card], card)
                    deck_image.text((90,70+20*row_count), (str(deck['Main Deck'][category][card])+" "+card), font=small_font, fill=(0, 0, 0))
                    row_count+=1
                row_count+=0.2
            elif (deck['Main Deck'][category] and category=='Lands'):
                row_count=1.7
                # print("\n"+category+":")
                deck_image.text((370,70+20*row_count), (category+":"), font=mid_font, fill=(0, 0, 0))
                row_count+=1
                for card in deck['Main Deck'][category]:
                    # print(deck['Main Deck'][category][card], card)
                    deck_image.text((370,70+20*row_count), (str(deck['Main Deck'][category][card])+" "+card), font=small_font, fill=(0, 0, 0))
                    row_count+=1
                row_count+=0.2
        row_count=1.7
        deck_image.text((600,70+20*row_count), ("Sideboard:"), font=mid_font, fill=(0, 0, 0))
        row_count+=1
        # print("\nSideboard: ")
        for card in deck['Sideboard']:
            current_card=(str(deck['Sideboard'][card][1])+" "+card)
            # print(deck['Sideboard'][card][1], card)
            deck_image.text((600,70+20*row_count), current_card, font=small_font, fill=(0, 0, 0))
            row_count+=1
        deck_background.save(f'deck_images/{deck_name}.png')

def logger(input):
    log_file=open("scanning_log.txt", "a")
    if input != []:
        input='ndf'
    match input:
        case []:
            log_file.write(f"No new events at {time.ctime()}\n")
        case 'ndf':
            log_file.write(f"New decks found at {time.ctime()}!\n")
        case _:
            return
    log_file.close()


delay_time=28800

while True: 
    start=time.perf_counter()
    card_of_interest="Ice-Fang Coatl"
    event_list=event_finder()
    new_events=event_comparer(event_list)
    desired_decks=event_parser(new_events, card_of_interest)
    organized_decks=deck_transformer(desired_decks)
    drawer(organized_decks)
    
    
    end_time=time.perf_counter()
    print(end_time-start)
    time.sleep(delay_time)