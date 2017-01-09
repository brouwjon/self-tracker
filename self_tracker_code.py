# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 20:58:54 2015

@author: Jon
"""
print ' '

import pickle
import datetime
import random
import Tkinter
from Tkinter import N,S,E,W
import ttk



core = {}
""" Dictionary mapping {strings:tag_instances} ...
... Essentially holds all important information (questions and response histories) ...
... See class(Tag) for more info """
groups = {}
""" Dictionary mapping {strings:group_instances} ... 
... Store related tags together ...
... Actual tag instances are NOT included here ...
... See class(Group) for more info """

global open_groups
open_groups = []
""" A list of Groups with unanswered Tags ...
... Updated after each tag response ...
... Used to get next group when answering Tag questions ...
... Is Saved / Imported each time at Close / Open """

all_groups = []
""" List of all Group names...
... Used for setting highlighted selection in Tkinter Listbox """

global today
today = datetime.date.today()
""" Current date ...
... Saved / Imported at close / open """



"""
####################################
#### Emergency functions Here ... 
####    Functions used as a last resort when Core / Groups are somehow corrupted beyond repair
####################################
"""

def updateGroupContents(groups):
    # Change group.content from list of pack instances to list of string names
    for gInstance in groups.values():
        newContent = []
        for tagInstance in gInstance.content:
            newContent.append(tagInstance.getTitle())
        gInstance.content = newContent
    return groups

def removeContentDuplicates(groups):
    # Remove duplicate tags from group contents
    for gInstance in groups.values():
        newContent = []
        for tag in gInstance.content:
            if tag not in newContent:
                newContent.append(tag)
        gInstance.content = newContent
    return groups
    
def resetAllTimelines(core):
    # Remove response history for all tags
    for tagInstance in core.values():
        tagInstance.clearTimeline()
    return core

def repairCore(tag):
    name = tag.getTitle()
    core[name] = tag
    
    
"""   
###################################
##### Saving & Importing Data #####
###################################
"""

def saveData(core, groups, date, open_groups):
    """ Pickle core, groups, date and open_groups ...
    ... Pickle to identically-named files in directory """    
    with open('core', 'w') as core_file:
        pickle.dump(core, core_file)
    with open('groups', 'w') as group_file:
        pickle.dump(groups, group_file)
    with open('date', 'w') as date_file:
        pickle.dump(date, date_file)
    with open('open_groups', 'w') as open_groups_file:
        pickle.dump(open_groups, open_groups_file)
    
def importData():
    """ UnPickle core, groups, date, and open_groups ...
    ... UnPickle from identically-named files in Directory """
    try:
        with open('core', 'r') as core_file:
            core = pickle.load(core_file)
    except EOFError:
        core = {}
    try:
        with open('groups', 'r') as group_file:
            groups = pickle.load(group_file)
    except EOFError:
        groups = {}
    try:
        with open('date', 'r') as date_file:
            date = pickle.load(date_file)
    except:
        date = datetime.date.today()
    try:
        with open('open_groups', 'r') as open_groups_file:
            open_groups = pickle.load(open_groups_file)
    except:
        open_groups = []
    return core, groups, open_groups, date 
    
    
"""  
###########################################
##### Create / Delete Groups and Tags #####
###########################################
"""
   
def makeGroup(groupName):
    # Add a key (type = string) to the "groups" dictionary
    # Does not add to open_group list, since new group has no tags
    assert type(groupName) == str
    groups[groupName] = group(groupName)
    all_groups.append(groupName)
    
def makeTag(title, question, group):
    # Adds tag instance to core dictionary... adds title (type = string) to group.content
    assert type(title) == str
    assert type(question) == str
    newTag = tag(title, question)
    core[title] = newTag
    try:
        group.addTag(newTag.getTitle())
    except:
        print "makeTag() 'group' parameter must be Group instance, not string"
        del core[title]
    return core

def deleteGroup(group):
    # Delete tags of group, and group
    groupName = group.getName()
    tags = groups[groupName].getContent()
    for t in tags:
        del core[t]
    del groups[groupName]
    all_groups.remove(groupName)
    if groupName in open_groups:
        open_groups.remove(groupName)
    
def deleteTag(tag):
    # Delete tag's info in respective group, update group instance in groups[] 
    # ... and remove tag from core
    group = tag.group
    tag_title = tag.getTitle()
    group.content.remove(tag_title)
    if tag_title in group.open_tags:
        group.open_tags.remove(tag_title)
    if group.open_tags == []:
        group.allAnswered = True
        if group.getName() in open_groups:
            open_groups.remove(group.getName())
    del core[tag_title]
    groups[group.getName()] = group
    

"""
#########################
##### DAY FUNCTIONS #####
#########################
"""

def set_to_yesterday():
    # Resets the day, and all groups / tags to yesterday's state... (open_groups & groups.open_tags)
    current_date = datetime.date.today() + datetime.timedelta(days = -1)
    open_groups = groups.keys()
    for group_name in groups:
        g = groups[group_name]
        g.open_tags = g.getContent()
        for tag_name in g.getContent():
            t = core[tag_name]
            if t.getLastDay() == current_date:
                g.open_tags.remove(tag_name)
        if len(g.open_tags) == 0:
            open_groups.remove(group_name)
        groups[group_name] = g
    return current_date, open_groups

def test_for_new_day(last_saved_date, open_groups):
    # Return fresh date & open_groups if application is launched for the first time today
    if datetime.date.today() == last_saved_date:
        # User is launching application for the second time on the same day
        # Do not update open_groups and data
        open_tags_dict = {g_name: groups[g_name].open_tags for g_name in groups}
        return last_saved_date, open_groups, open_tags_dict
    else:
        # user is launching application for the first time today 
        new_current_date = datetime.date.today()
        new_open_groups = groups.keys()
        open_tags_dict = {g_name: groups[g_name].getContent() for g_name in groups}
        return new_current_date, new_open_groups, open_tags_dict

        
        
        
"""        
###################################      
##### Groups, Tags, Responses #####
###################################
"""

""" GROUPS """
        
class group(object):
    """
    *** COLLECTION OF RELATED TAGS ***
    Does NOT store tag instances ... only provides Tag names to retrieve FROM CORE
    Contains list of included Tag names (self.content) ... 
    ... and tracks which Tags have NOT yet been answered (self.open_tags)
    """
    def __init__(self, name):
        self.name = name
        self.allAnswered = False
        self.content = []
        self.open_tags = []
    
    ##########################
    ####  GETTER METHODS  ####
    ##########################       
        
    def getContent(self):
        self.content.sort()
        return self.content[:]
    
    def getOpenTags(self):
        return self.open_tags[:]
            
    def getTag(self, tagName):
        #Return tag instance, given its name
        assert type(tagName) == str
        tag = core[tagName]
        return tag
    
    def getName(self):
        return self.name
    
    def isAllAnswered(self):
        return self.allAnswered
    
    def getNextUnanswered(self):        
        next_tag_name = self.open_tags[0]
        return core[next_tag_name]
        
    ##########################
    ####  SETTER METHODS  ####
    ##########################        
        
    def addTag(self, tagName):
        # Adds a tag to self.content, and creates a key:value pair for it in core
        assert type(tagName) == str
        core[tagName] = tag(tagName, self)          # Create Tag in core
        self.allAnswered = False
        for obj in [self.content, self.open_tags]:
            obj.append(tagName)
            obj.sort()
        if self.getName() not in open_groups:
            open_groups.append(self.getName())
        groups[self.getName()] = self               # update self's name in group dictionary
    
    def setName(self, newName):
        # Delete and update self.name in groups[] dict and open_groups lisgt
        assert type(newName) == str
        del groups[self.name]
        in_open_groups = None
        if self.name in open_groups:                # Save self's "open_groups" state to replace with new name, if necessary
            in_open_groups = True
            open_groups.remove(self.getName())
        self.name = newName
        if in_open_groups == True:
            open_groups.append(self.getName())
        groups[self.getName()] = self
    
    #############################
    ####  OPERATION METHODS  ####
    #############################
    
    def markChecked(self, tag):
        # Mark a tag as "answered" by removing it from self.open_tags 
        if tag in self.open_tags:                       # case: Tag won't be in self.open_tags...
            self.open_tags.remove(tag)                  # ... during an overwrite() operation
        if self.open_tags == []:
            self.allAnswered = True
            if self.getName() in open_groups:
                open_groups.remove(self.getName())
        groups[self.getName()] = self
    
    def refreshOpenTags(self):
        # Ensures all tags in self.open_tags have not been answered today
        new_open_tags = []
        for tag_name in self.getContent():
            t = core[tag_name]
            if t.getLastDay() != today or t.getLastDay() == None:
                new_open_tags.append(t.getTitle())
        self.open_tags = new_open_tags
        if self.open_tags == []:
            self.isAllAnswered = True


""" TAGS """
        
class tag(object):
    """
    A question with up to 4 user-defined responses, to be answered daily ...
    Tags have "Titles" and "Questions" ...
        ... Titles are short words/phrases displayed in Listbox ...
        ... Questions are what the user will respond to 
    Each Tag is associated with a Group
    Tags have "TimeLines", which keep track of the user's responses each day
    Tags can only be answered once per day, but the response can be overwritten
    """  
    
    def __init__(self, title, group):
        self.title = title
        self.group = group
        self.question = "This tag doesn't have a question yet"
        self.timeLine = timeLine(self)
        self.options = {1:None, 2:None, 3:None, 4:None}
        self.used_options = 0
        
    def __str__(self):
        return self.title
        
###########################        
##    GETTER FUNCTIONS   ##
###########################
    
    def getTitle(self):
        return self.title
        
    def getQuestion(self):
        return self.question   
        
    def getLastResponse(self):
        """ Returns the text of the last chosen response """ 
        if self.timeLine.lastEntry == None:
            return None
        else:
            return self.options[self.timeLine.lastEntry]
    
    def getLastDay(self):
        """ Returns last datetime.date saved in Timeline ... 
        ... "None" if tag has no response yet """
        return self.timeLine.getLastDay()   
    
    def lastDayForSlot(self, slot):
        """ Returns last datetime.date for a specific response slot """
        if self.timeLine.data[slot] == []:
            return None
        else:
            return self.timeLine.data[slot][-1]

    def getOptions(self):
        """ Returns list of strings (text for each response) """
        return self.options.values()    
    
    def getGroup(self):
        return self.group
       
###########################         
##    SETTER FUNCTIONS   ##
###########################        
        
    def addOption(self, response):
        # Add a response option to the tag 
        if self.used_options == 4:              #Make sure self.options isn't full
            print "No room in options"
            assert False
        for slot in self.options:               #Find empty option slot
            if self.options[slot] == None:
                self.options[slot] = response   #Set it to response
                break
        self.used_options += 1
        core[self.getTitle()] = self
        
    def editOption(self, slot, newText):
        # Change the text of a specified response option
        self.options[slot] = newText  
        core[self.getTitle()] = self              

    def removeOption(self, slot):
        """ Remove response option (text)) and timeLine data ... 
        ... reset slot positions for the remaining responses """
        # Remove response and its timeline data
        self.options[slot] = None
        self.timeLine.emptyHistory(slot)
        self.used_options -= 1
        # Save remaining reponses and histories (response text & list of dateTimes)
        options_and_history = []
        for k in self.options:
            if self.options[k] != None:
                o = self.options[k]                     # response option  
                h = self.timeLine.data[k]               # response history           
                options_and_history.append((o, h))
            # delete response/history in current sequence
            self.options[k] = None
            self.timeLine.emptyHistory(k)
        # Reset response and timeLine slots
        for i in range(len(options_and_history)):
            response_text = options_and_history[i][0]
            response_timeLine = options_and_history[i][1]
            self.options[i + 1] = response_text
            self.timeLine.data[i + 1] = response_timeLine
        core[self.getTitle()] = self
        
    def undoLastResponse(self):
        # Remove last response from timeLine
        self.timeLine.undoLast()
        core[self.getTitle()] = self
        
    def changeTitle(self, newTitle):
        # Remove old self.title from group and core        
        old_title = self.getTitle()        
        self.group.content.remove(old_title)
        del core[old_title]
        # remove tag from group.open_tags, if need be
        in_open_tags = None
        if self.getTitle() in self.group.getOpenTags():
            in_open_tags = True
            self.group.open_tags.remove(self.getTitle())
        # add new self to group and core
        self.title = newTitle
        self.group.content.append(newTitle)
        if in_open_tags == True:
            self.group.open_tags.append(newTitle)           # put newTitle in group.open_tags, if need be
        groups[self.group.getName()] = self.group
        core[newTitle] = self
    
    def changeQuestion(self, newQuestion):
        if type(newQuestion) != str:
            raise "Question not a string"
        self.question = newQuestion
        core[self.getTitle()] = self


#################################
##### "OPERATION FUNCTIONS" #####
#################################

    def respond(self, choice):
        # Log a response in [choice] data slot
        if choice == None:
            print "tag.respond() ... choice == None"
        self.timeLine.updateResponse(choice)
        self.group.markChecked(self.getTitle())
        core[self.getTitle()] = self
        groups[self.getGroup().getName()] = self.getGroup()
    
    def clearOptions(self):
        # Delete the TEXT of possible response options
        self.options = {1:None, 2:None, 3:None, 4:None}
        core[self.getTitle()] = self
    
    def clearTimeline(self):
        # Delete response DATA from all question entires
        self.timeLine = timeLine(self)   
        core[self.getTitle()] = self
    
    def deleteLastResponse(self):
        self.timeLine.undoLast()
        core[self.getTitle()] = self



""" TIMELINE """
        
class timeLine(object):
    """
    Catalog of accumulated responses to a tag 
    Can hold up to 4 response slots
    {Number 1-4 (response) : [list of datetime.dates]}
    Each number in self.data is a response option to the respective tag
    Length of list == number of times response was chosen
    --methods-- 
    add / remove log
    get last log time / num
    """    
    
    def __init__(self, tag):
        self.tag = tag                              # "who this belongs to"
        self.data = {1:[], 2:[], 3:[], 4:[]}        # dict {responses:list of times chosen}
        self.lastEntry = None                       # saves last response number
        
    def updateResponse(self, entry):
        # Add a datetime.date to whichever response the user chose
        self.lastEntry = entry                       # save the last response
        self.data[entry].append(today)
        self.data[entry].sort()

    def getLastDay(self):
        # Return the datetime.date of last entry
        if self.lastEntry == None:
            return None
        elif self.data[self.lastEntry] == []:
            return None
        else:
            return self.data[self.lastEntry][-1]
    
    def undoLast(self):
        # Remove last the last item added to the data lists
        if self.lastEntry == None:                      # case: There is no last response
            return None
        self.data[self.lastEntry].pop()                 # Remove last response  
        if self.data.values() == [ [],[],[],[] ]:       # case: All responses removed
            self.lastEntry = None
        else:                                     # basic case: Find new self.lastEntry
            most_recent_entry = 1
            for key in range(2,5):
                if self.data[key] > self.data[most_recent_entry]:
                    most_recent_entry = key
            self.lastEntry = most_recent_entry

    def emptyHistory(self, slot):
        # Sets a self.data slot back to []
        del self.data[slot]
        self.data[slot] = []
        # Update self.lastEntry
        if self.data == {1:[], 2:[], 3:[], 4:[]}:         # If there are no previous responses, set lastEntry as None
            self.lastEntry = None
        elif self.lastEntry == slot:                      # If lastEntry was slot, Find previous lastEntry
            last_entry_dict = {}
            for slot in range(1,5):
                if self.data[slot] != []:
                    last_entry_dict[slot] = self.data[slot][-1]
            self.lastEntry = min(last_entry_dict)
                
        
        
        
        
        
        



"""
#######################
##### TKINTER GUI #####
#######################
"""

class myFrame(ttk.Frame):
    
    """ Entire GUI is a custom Frame subclass ... 
    ... this method was chosen because of my familiarity with it from a tutorial
    
    ... The GUI is organized in 2 sections-- an upper and a lower
    ... Upper section is Listboxes of Group, Tags, Responses ...
        ... Response Listbox displays responses of currently selected Tag
        ... Tag Listbox displays Tags of currently selected Group
        ... User may navigate this section entirely with arrowkeys
    ... Lower section has buttons for Groups / Tags / Responses ...
        ... Typically the buttons are Add, Edit, or Remove
        
    ... Groups / Tags / Responses are marked with an "X" if they have been used that day
        ... Answering a Tag or closing a Group will immediately move to the next open one
    
    ... Groups / Tags / Responses will typically be referenced as "GTR"
    """
    
    
    
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.master.title("Self Tracker")
        
        self.initUI()
        
    
    def initUI(self):
        """
        Pack frame, initialize and grid all widgets, bind functions as needed
        """
        self.grid()
        
        ###################
        ##### Widgets #####
        ###################
        
        # Labels for Group & Tag Listboxes, selected tag Question
        # Tag Question field is changed each time new tag is selected...
        # ... use control variable
        self.GroupHeader = ttk.Label(self, text = 'Groups', font='bold')
        self.TagHeader = ttk.Label(self, text = 'Tags', font='bold')
        self.TAG_QUESTION_TEXT = Tkinter.StringVar(self, value = '')
        self.tag_question = ttk.Label(self, textvariable = self.TAG_QUESTION_TEXT)
        self.responseInfo = ttk.Label(self, text = 'Response Operations', font='bold')
        self.commandLabel = ttk.Label(self, text = "Input / Output", font='bold')
        
        

        """ CREATE BUTTONS """ 
        
        self.quitButton = ttk.Button(self, text = "Quit", command = self.save_and_quit)
        self.enter = ttk.Button(self, text = "Enter")
        self.respond = ttk.Button(self, text = "Respond", command = self.answer_tag)
        self.overWrite = ttk.Button(self, text = "Overwrite")
        self.resetDay = ttk.Button(self, text = "Reset Day", command = self.reset_day)
        
        self.addGroup = ttk.Button(self, text = "Add Group", command = self.add_group)
        self.addTag = ttk.Button(self, text = "Add Tag", command = self.add_tag)
        self.addOption = ttk.Button(self, text = "Add Option", command = self.add_option)
        
        self.editGroup = ttk.Button(self, text = "Edit Group Name", command = self.edit_group_name)
        self.editTagName = ttk.Button(self, text = "Edit Tag Name", command = self.edit_tag_name)
        self.editTagQuestion = ttk.Button(self, text = "Edit Tag Question", command = self.edit_tag_question)
        self.editOption = ttk.Button(self, text = "Edit Option", command = self.edit_option)
        
        self.removeGroup = ttk.Button(self, text = "Remove Group", command = self.remove_group)
        self.removeTag = ttk.Button(self, text = "Remove Tag", command = self.remove_tag)
        self.removeOption = ttk.Button(self, text = "Remove Option", command = self.remove_option)
        
        
        
        """ CONTROL VARIABLES """ 
        
        self.CIN = Tkinter.StringVar(self, value = '')
            # Variable tied to Entry widget... used to retrieve user input
        self.COUT = Tkinter.StringVar(self, value = '')
            # .... Used to display text & prompts to user
        self.CURRENT_ITEM = Tkinter.IntVar(self, value = 0)
            # int between [0,2] ... tracks which panel the user is in
            # {0:Group, 1:Tag, 2:Response}
            # used in navigate() function... mostly to set Tkinter focus
        self.TAG_REPONSE_NUM = Tkinter.IntVar(self, value=0)
        self.USER_COMMAND = Tkinter.StringVar(self, value = '')
        
        
        
        """ CURRENTLY SELECTED GROUP / TAG  *INSTANCES* ...
        ... changed each time user clicks or navigates to new item """
        
        self.selected_group = None
        self.selected_tag = None
        self.selected_response = None
        
#        # Group and Tag lists displayed in Listboxes
#        self.ACTIVE_GROUPS = []
#        self.TAGS_OF_GROUP = []
        
        
        
        """ LISTBOXES FOR DISPLAYING / SELECTING GROUPS, TAGS, RESPONSES """
        
        # Group & Tag Listboxes
        self.Group_Listbox = Tkinter.Listbox(self, selectmode = "browse", exportselection = False)
        self.Tag_Listbox = Tkinter.Listbox(self, selectmode = "browse", exportselection = False)
        self.Response_Listbox = Tkinter.Listbox(self, selectmode = "browse", exportselection = False)
        # Bind Listbox events for selection and navigation
        self.Group_Listbox.bind('<<ListboxSelect>>', self.get_selected_group)
        self.Group_Listbox.bind('<Right>', self.navigate)
        self.Tag_Listbox.bind('<<ListboxSelect>>', self.get_selected_tag)
        self.Tag_Listbox.bind('<Right>', self.navigate)
        self.Tag_Listbox.bind('<Left>', self.navigate)
        self.Response_Listbox.bind('<<ListboxSelect>>', self.get_selected_response)
        self.Response_Listbox.bind('<Left>', self.navigate)
        
        # !!! Commands in/out (CIN/COUT)
        self.consoleIn = ttk.Entry(self, textvariable = self.CIN)
        self.consoleOut = ttk.Label(self, textvariable = self.COUT)
                
                
        """       
        ########################
        ##### Grid Widgets #####
        ########################
        """
                
        # Set minimum size of column w/response radiobuttons
        self.columnconfigure(4, minsize = 200)
        self.rowconfigure(11, minsize=15)
                
        # Headers / Titles / Labels / Listboxes
        self.GroupHeader.grid(row=0, column=0, columnspan=2, pady=5) 
        self.Group_Listbox.grid(row=1, column=0, rowspan=4, columnspan=2, sticky = E+W)
        self.TagHeader.grid(row=0, column=2, columnspan=2)
        self.Tag_Listbox.grid(row=1, column=2, rowspan=4, columnspan=2, sticky = E+W)
        self.tag_question.grid(row=0, column=4)
        self.responseInfo.grid(row = 7, column=4, columnspan=2, pady=5)
        self.Response_Listbox.grid(row=1, column=4, rowspan=4, columnspan=2, sticky = E+W)
        self.commandLabel.grid(row=7,column=0, columnspan=2)
        
        # GTR: Add / Edit / Remove
        self.addGroup.grid(row=5, column=0, rowspan=2, sticky=N+S, ipadx=10, ipady=10)
        self.editGroup.grid(row=5, column=1)
        self.removeGroup.grid(row=6, column=1, sticky=W+E)
        self.addTag.grid(row=5, column=2, rowspan=2, sticky=N+S)
        self.editTagName.grid(row=5, column=3, sticky=W+E)
        self.editTagQuestion.grid(row=6, column=3, sticky=W+E)
        self.removeTag.grid(row=7, column=3, sticky=N+W+E)
        self.addOption.grid(row=8,column=4, sticky=W+E)
        self.editOption.grid(row=9,column=4, sticky=W+E)
        self.removeOption.grid(row=10,column=4, sticky=W+E)
        
        # Data in/out, quit, etc...
        self.respond.grid(row=5,column=4,rowspan=2, sticky=N+S+E+W)
        self.overWrite.grid(row=5,column=5,rowspan=2, sticky=N+S+W+E)
        self.consoleOut.grid(row=8,column=0, columnspan=4, sticky = W, padx=5)
        self.consoleIn.grid(row=9,column=0, columnspan=2)
        self.quitButton.grid(row=10,column=0, rowspan=2, sticky=N+S+E+W)
        self.enter.grid(row=10,column=1, rowspan=2, sticky=N+S+E+W)
        self.resetDay.grid(row=10, column=2, rowspan=2, sticky=N+S+E+W)
        
        self.update_group_list()
        self.Group_Listbox.focus_set()
        
        
        
        
        """
        #################################
        ########### FUNCTIONS ###########
        #################################
        """
        
    def save_and_quit(self):
        """ function bound to quitButton """
        saveData(core, groups, today, open_groups)
        self.master.destroy()
    
    def reset_day(self):
        # Sets date, and status of all GTR's, to yesterday
        global today
        global open_groups
        today, open_groups = set_to_yesterday()
        self.selected_group, self.selected_tag, self.selected_response = None, None, None
        self.update_group_list()
        self.Group_Listbox.focus_set()
        self.Tag_Listbox.delete(0, Tkinter.END)
        self.Response_Listbox.delete(0, Tkinter.END)
    
    def selected_group_index(self):
        # Finds index (in list all_groups) of currently selected group...
        # ... Used to set Listbox selection highlight when group name changes
        if self.selected_group == None:
            print "self.selected_group_index()... this function was called when no group was selected"
            return None
        for index in range(len(all_groups)):
            if all_groups[index] == self.selected_group.getName():
                return index
        return None
    
    def selected_tag_index(self):
        # Finds index of current selected tag in group.content
        if self.selected_tag == None:
            print "self.selected_tag_index() called when no tag was selected"
            return None
        content = self.selected_group.getContent()[:]
        for index in range(len(content)):
            if content[index] == self.selected_tag.getTitle():
                return index
        print "tag index = None"
        return None        
    
    
    def navigate(self, evt):
        """ Move highlighted selection ACROSS  GTR listboxes...
        ... sets <Return> key to answer_tag when moving into response_listbox 
        ... If user is in Group_Listbox, then no Tag or Response is selected... same for tag > response"""
        
        direction = evt.keysym
        if direction == "Right" and self.CURRENT_ITEM < 2:
            self.CURRENT_ITEM += 1
        elif direction == "Left" and self.CURRENT_ITEM > 0:
            self.CURRENT_ITEM -= 1

        if self.CURRENT_ITEM == 0:
            # Navigate to Group_Listbox
            self.selected_tag, self.selected_response = None, None
            self.Group_Listbox.focus_set()
            self.Group_Listbox.selection_clear(0, Tkinter.END)
            if self.selected_group != None:                         # If there is a selected group
                index = self.selected_group_index()
                self.Group_Listbox.selection_set(index)
                self.Group_Listbox.event_generate('<<ListboxSelect>>')  
            elif all_groups == []:                                  # if there are no groups
                pass
            else:                                                   # highlight first group
                self.Group_Listbox.selection_set(0)
                self.Group_Listbox.event_generate('<<ListboxSelect>>') 
        elif self.CURRENT_ITEM == 1:
            # Navigate to Tag_Listbox
            self.selected_response = None
            self.Tag_Listbox.focus_set()
            self.Tag_Listbox.selection_clear(0, Tkinter.END)
            if self.selected_tag != None:
                index = self.selected_tag_index()
                self.Tag_Listbox.selection_set(index)
                self.Tag_Listbox.event_generate('<<ListboxSelect>>')
            elif self.selected_group.getContent() == []:
                pass
            else:
                self.Tag_Listbox.selection_set(0)
                self.Tag_Listbox.event_generate('<<ListboxSelect>>')
        elif self.CURRENT_ITEM == 2:
            # Navigate to Response_Listbox
            self.Response_Listbox.focus_set()
            self.Response_Listbox.selection_clear(0, Tkinter.END)
            if self.selected_response != None:
                index = self.selected_response - 1
                self.Response_Listbox.selection_set(index)
                self.Response_Listbox.event_generate('<<ListboxSelect>>')
            elif self.selected_tag.getOptions() == []:
                pass
            else:
                self.Response_Listbox.selection_set(0)
                self.Response_Listbox.event_generate('<<ListboxSelect>>')
    
    def move_to_next_item(self):
        # Selects and displays the next GTR after user makes a response
        if open_groups[:] == []:                                # Exhausted ALL tags
            self.COUT.set("All tags answered")
            self.Response_Listbox.unbind('<Return>')
        elif self.selected_group.isAllAnswered() == True:       # Group completed, move to next
            next_group_name = open_groups[0]
            self.selected_group = groups[next_group_name]
            self.selected_tag = self.selected_group.getNextUnanswered()
            self.selected_response = None
            if self.selected_tag.getOptions() != None:          # if next tag has any responses
                self.selected_response = 1
                self.Response_Listbox.focus_set()
                self.Response_Listbox.bind('<Return>', self.quick_respond)
        else:                                                   # Get next tag in current group
            self.selected_tag =  self.selected_group.getNextUnanswered()
            self.selected_response = None
            if self.selected_tag.getOptions() != None:
                self.selected_response = 1
                self.Response_Listbox.focus_set()
                self.Response_Listbox.bind('<Return>', self.quick_respond)
        self.update_group_list()
        self.update_tag_list()
        self.update_response_list()
    
    
    
    """
    ############################
    ##### UPDATE GTR LISTS #####
    ############################
    """
     
    def update_group_list(self):
        """
        Update Group_Listbox's content
        Mark groups with "X" if they are completely answered
        """
        all_groups.sort()
        self.Group_Listbox.delete(0, Tkinter.END)               # clear old listbox content
        for i in range(len(all_groups)):                        # add all items in all_groups
            group_name = all_groups[i]
            if group_name in open_groups:
                self.Group_Listbox.insert(i, group_name)
            else:
                self.Group_Listbox.insert(i, "X " + group_name) # mark with "X" if answered
        if self.selected_group != None:
            index = self.selected_group_index()                 
            self.Group_Listbox.selection_set(index)             # highlight self.selected_group
    
    def update_tag_list(self):
        """
        Displays self.selected_group's tags in Tag_Listbox
        Marks answered tags with an "X" 
        """
        tag_list = self.selected_group.getContent()[:]                        # get all tags of selected group
        open_tags = self.selected_group.getOpenTags()                         # get list of unanswered tags
        self.Tag_Listbox.delete(0, Tkinter.END)                 # clear old listbox content
        for i in range(len(tag_list)):                          # add all tags to listbox
            tag_name = tag_list[i]
            if tag_name in open_tags:
                self.Tag_Listbox.insert(i, tag_name)
            else:
                self.Tag_Listbox.insert(i, "X " + tag_name)     # mark with "X" if answered
        if self.selected_tag != None:
            index = self.selected_tag_index()
            self.Tag_Listbox.selection_set(index)               # highlight self.selected_tag

    def update_response_list(self):
        """
        Displays selected tag's responses... 
        Marks response with "X" if it was used as today's answer 
        """
        tag = self.selected_tag
        self.Response_Listbox.delete(0, Tkinter.END)
        valid_responses = []
        for r in tag.options:                               # get only the *Defined* responses
            if tag.options[r] != None:    
                valid_responses.append((r, tag.options[r])) # list of tuples (key: text)
        for pair in valid_responses:                        # mark answered responses with "X"
            key = pair[0]                                   # key in tag.options (dict) for this response
            index = key - 1                                 # index to be placed in Listbox
            text = '   ' + pair[1]
            if tag.lastDayForSlot(key) == today:        
                self.Response_Listbox.insert(index, "X" + text[2:])     # mark answered with "X"
            else:
                self.Response_Listbox.insert(index, text)
        if self.selected_response != None:
            index = self.selected_response - 1
            self.Response_Listbox.selection_set(index)
        
        
        
        
    """    
    ##############################
    ###### GET SELECTED GTR ######
    ##############################
    """
    
    def get_selected_group(self, evt):
        """
        ... Bound function of Group_Listbox... 
        ... Finds group instance through listbox index
        """
        # Set self.selected_group
        widget = evt.widget
        index = int(widget.curselection()[0])
        selected_group_name = widget.get(index)
        if selected_group_name[0:2] == "X ":                        # if group marked with "X "...
            selected_group_name = selected_group_name[2:]           # ... (not in open_groups)
        self.selected_group = groups[selected_group_name]
        self.selected_tag, self.selected_response = None, None
        self.CURRENT_ITEM = 0                               # set control variable used by navigate()
        self.update_tag_list()
        self.Response_Listbox.delete(0, Tkinter.END)        # show no responses if tag no selected

    def get_selected_tag(self, evt):
        """ 
        ... Bound function of Tag_Listbox...
        ... Sets self.selected_tag as tag chosen in Tag_Listbox...
        """
        # Get selected tag
        widget = evt.widget
        index = int(widget.curselection()[0])
        selected_tag_name = widget.get(index)
        if selected_tag_name[0:2] == "X ":
            selected_tag_name = selected_tag_name[2:]
        self.selected_tag = core[selected_tag_name]
        self.CURRENT_ITEM = 1                               # set control variable used by navigate()
        self.TAG_QUESTION_TEXT.set(self.selected_tag.getQuestion())
        self.update_response_list()                         # Set Radiobutton texts
    
    def get_selected_response(self, evt):
        """
        ... Bound function of Response_Listbox...
        ... Since tag response options are saved in a dictionary with keys [1,4]...
                ... sets self.selected_response to index+1
        """
        widget = evt.widget
        index = int(widget.curselection()[0])
        response_slot = index + 1
        self.selected_response = index + 1
        self.CURRENT_ITEM = 2                               # set control variable used by navigate()
        
        # bind <Return> for quick response if this tag was not used already today
        if self.selected_tag.lastDayForSlot(response_slot) != today:    
            self.Response_Listbox.bind('<Return>', self.quick_respond)
        # UN-bind <Return> if this response was used today
        elif self.selected_tag.lastDayForSlot(response_slot) == today:
            self.Response_Listbox.unbind('<Return>')
            
            
            
    
    """
    ##############################
    ###### Button Functions ######
    ##############################
    """
    
    def answer_tag(self):
        # Responds to selected_tag with selected_response, 
        user_choice = self.selected_response
        tag = self.selected_tag
        if tag.getLastDay() == None:
            pass
        elif tag.getLastDay() == today:                         # Allow user to overwrite day's response
            self.COUT.set("You've already responded to this tag today... overwrite?")
            self.overWrite.bind('<Button-1>', self.overwrite)
            # TODO: Unbind the overwrite button if user says no
            return None
        self.selected_tag.respond(user_choice)
        self.move_to_next_item()

    def quick_respond(self, event):
        """ Need this function to accept a <Return> event to respond to a tag...
        ... because self.answer_tag() doesn't accept an event argument..."""
        # Do nothing with event
        self.answer_tag()

    def overwrite(self, evt):
        """ Called when user wants to overwrite a tag's response for the current day...
        ... removes self.selected_tag's last logged response, then calls answer_tag() """ 
        self.COUT.set('')
        self.selected_tag.deleteLastResponse()
        self.answer_tag()

    def bind_buttons(self, function, text):
        """ An 'efficiency' function meant to execute repetitive code...
        ... Using this function, GUI buttons do nothing except bind the real function to the <Return> key (or Enter button)
        ... Prompts user with given text, places Window focus on the Entry...
        ... binds <Return> key and enterButton to the given function """ 
        self.COUT.set(text)
        self.consoleIn.focus_set()
        self.consoleIn.bind('<Return>', function)
        self.enter.bind('<Button-1>', function)




    """
    ###############################
    ##### ADD/EDIT/REMOVE GTR #####
    ###############################
    
        << NOTE ON FUNCTIONS' STRUCTURE >>
        
    function_name(): Gives the user a prompt, then binds the appropriate function to the "Enter" button
    function_name_exe(): Executes the function upon Enter button-click
    """
    
    """ ADD """

    def add_group(self):
        self.bind_buttons(self.add_group_exe, 'Enter the name of your new group')
    def add_group_exe(self, evt):
        group_name = self.CIN.get()
        self.COUT.set('')
        self.CIN.set('')
        makeGroup(group_name)
        self.selected_group = groups[group_name]
        self.selected_tag = None
        self.selected_response = None
        self.update_group_list()
        self.Tag_Listbox.delete(0, Tkinter.END)
      
    def add_tag(self):
        self.bind_buttons(self.add_tag_exe, 'Enter name of the tag to be added to this group')
    def add_tag_exe(self, evt):
        group = self.selected_group
        tag_name = self.CIN.get()
        self.COUT.set('')
        self.CIN.set('')
        group.addTag(tag_name)
        self.selected_tag = core[tag_name]
        self.selected_group = groups[group.getName()]
        self.update_group_list()
        self.update_tag_list()
        self.Response_Listbox.delete(0, Tkinter.END)
        
    def add_option(self):
        self.bind_buttons(self.add_option_exe, "Enter text of your new response option")
    def add_option_exe(self, evt):
        tag = self.selected_tag
        optionText = self.CIN.get()
        self.COUT.set('')
        self.CIN.set('')
        tag.addOption(optionText)
        self.selected_group = groups[self.selected_group.getName()]
        self.selected_tag = core[tag.getTitle()]
        self.selected_response = tag.used_options
        self.update_group_list()
        self.update_tag_list()
        self.update_response_list()
        self.Response_Listbox.focus_set()


    """ EDIT """

    def edit_group_name(self):
        self.bind_buttons(self.edit_group_name_exe, 'Enter the new name of this group')
    def edit_group_name_exe(self, evt):
        """ calls group.setName() function... which does all the heavy lifting 
        ... repopulates group_listBox ... """
        new_name = self.CIN.get()                               # retrieve new group title from Entry widget
        old_name = self.selected_group.getName()
        self.COUT.set('')  
        self.CIN.set('')
        all_groups.remove(old_name)
        if old_name in open_groups:
            open_groups.remove(old_name)
            open_groups.append(new_name)
        self.selected_group.setName(new_name)
        all_groups.append(new_name)
        self.update_group_list()
            
    def edit_tag_name(self):
        self.bind_buttons(self.edit_tag_name_exe, "Enter new title of this tag")
    def edit_tag_name_exe(self, evt):
        newTitle = self.CIN.get()
        self.COUT.set('')
        self.CIN.set('')
        self.selected_tag.changeTitle(newTitle)
        self.selected_group = groups[self.selected_group.getName()]
        self.update_tag_list()
        
    def edit_tag_question(self):
        self.bind_buttons(self.edit_tag_question_exe, "Enter text of new question")
    def edit_tag_question_exe(self, evt):
        newQuestion = self.CIN.get()
        self.COUT.set('')
        self.CIN.set('')
        self.selected_tag.changeQuestion(newQuestion)
        self.TAG_QUESTION_TEXT.set(newQuestion)
        
    def edit_option(self):
        self.bind_buttons(self.edit_option_exe, "Select response to edit, and enter new text")
    def edit_option_exe(self, evt):
        new_text = self.CIN.get()
        self.COUT.set('')
        self.CIN.set('')
        self.selected_tag.editOption(self.selected_response, new_text)
        self.update_response_list()
        
        
    """ REMOVE """
    
    def remove_group(self):
        self.bind_buttons(self.remove_group_exe, "Select group you want to remove, then press enter")
    def remove_group_exe(self, evt):
        deleteGroup(self.selected_group)
        self.COUT.set('')  
        self.CIN.set('')
        self.selected_group = None
        self.selected_tag = None
        self.update_group_list()
        self.Tag_Listbox.delete(0, Tkinter.END)
        self.Response_Listbox.delete(0, Tkinter.END)
        
    def remove_tag(self):
        self.bind_buttons(self.remove_tag_exe, "Select tag you want to remove, then press enter")
    def remove_tag_exe(self, evt):
        save_group_name = self.selected_group.getName()              # save groupName for update, after delete tag
        deleteTag(self.selected_tag)
        self.COUT.set('')  
        self.CIN.set('')
        self.selected_group = groups[save_group_name]
        self.selected_tag = None
        self.selected_response = None
        self.update_tag_list()
        self.update_group_list()
        self.Response_Listbox.delete(0, Tkinter.END)
        
    def remove_option(self):
        self.bind_buttons(self.remove_option_exe, "Select the option you want to remove")
    def remove_option_exe(self, evt):     
        selected_option = self.selected_response
        self.selected_tag.removeOption(selected_option)
        self.selected_tag = core[self.selected_tag.getTitle()]
        # update Group and Tag status in open_groups & group.open_tags, respectively
        self.selected_group.refreshOpenTags()
        groups[self.selected_group.getName()] = self.selected_group
        if self.selected_group.isAllAnswered == False:
            global open_groups
            open_groups = list( set(open_groups).add( self.selected_group.getName() ) )
        open_groups.append(self.selected_group.getName())
        # update Listboxes
        self.update_group_list()
        self.update_tag_list()
        self.update_response_list()
        self.COUT.set('')  
        self.CIN.set('')
    
    """
    ########################
    ##### END GUI CODE #####
    ########################
    """



""" USE THIS IF YOU HAVE NO SAVED DATA """
#today = datetime.date.today()

""" LOAD GROUPS & CORE FROM SAVED DATA """
# Load the tags, groups, and date
core, groups, date, open_groups = importData()
#date = datetime.date.today() + datetime.timedelta(days = -1)
#open_groups = {}
# If it is a new day, mark all groups & tags as open
today, open_groups, open_tags_dict = test_for_new_day(date, open_groups)
all_groups = groups.keys()[:]
for g_name in open_tags_dict:
    groups[g_name].open_tags = open_tags_dict[g_name]



def gui():
    root = Tkinter.Tk()
    example = myFrame(root)
    root.mainloop()
    
if __name__ == '__main__':
    gui() 


#""" FAKE TESTING DATA """
#group_list = ['g1', 'g2']
#tag_list = ['t1', 't2']
#response_list = ['r1','r2']
## make groups
#for g in group_list:
#    makeGroup(g)
## add tags to all groups
#for i in range(len(group_list)):
#    g_text = group_list[i]
#    t_text = tag_list[i]
#    g = groups[g_text]
#    g.addTag(g_text + t_text)
## add responses to all tags
#for i in range(len(response_list)):
#    g_text = group_list[i]
#    t_text = tag_list[i]
#    r_text = response_list[i]
#    t = core[g_text + t_text]
#    t.addOption(g_text + t_text + r_text)
    
"""
k = groups.values()
for g in k:
    if tag in g.open_tags:
        g.open_tags.remove(tag)
    if tag in g.content:
        g.content.remove(tag)
"""

"""
save_dict = {}
for g in groups:
    save_dict[g] = groups[g].getContent()
"""

"""
for gName in data:
    g = group(gName)
    all_groups.append(gName)
    tags = data[gName]
    for t in tags:
        g.addTag(t)
"""
