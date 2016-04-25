"""
Upgrade of the python client for freesound

Find the API documentation at http://www.freesound.org/docs/api/.

This lib provides method for managing files and data with a local data storage
"""

import copy
import freesound
import os
import json
import ijson

LENGTH_BAR = 30

class SettingsSingleton(object):
    class __OnlyOne:
        def __init__(self):
            self.local_sounds = []
            self.local_analysis = []
            self.local_baskets = []
    instance = None
    def __new__(cls): # __new__ always a classmethod
        if not SettingsSingleton.instance:
            SettingsSingleton.instance = SettingsSingleton.__OnlyOne()
        return SettingsSingleton.instance
    def __getattr__(self, name):
        return getattr(self.instance, name)
    def __setattr__(self, name):
        return setattr(self.instance, name)



class Client(freesound.FreesoundClient):
    """
    Create FreesoundClient and set authentification
    
    """

    def scan_folder(self):
        settings = SettingsSingleton()

        # Check if the storing folder are here
        if not os.path.exists('sounds'):            
            os.makedirs('sounds')
        if not os.path.exists('analysis'):
            os.makedirs('analysis')
        if not os.path.exists('baskets'):
            os.makedirs('baskets')
                
        # create variable with present local sounds & analysis 
        # (reduce time consumption for function loading json files)
        files_sounds = os.listdir('./sounds/')
        files_analysis = os.listdir('./analysis/')
        files_baskets = os.listdir('./baskets/')

        settings = SettingsSingleton()
        settings.local_sounds = []
        settings.local_analysis = []
        settings.local_baskets = []

        for i in files_sounds:
            settings.local_sounds.append(int(i[:-5]))
        for j in files_analysis:
            settings.local_analysis.append(int(j[:-5]))
        for m in files_baskets:
            settings.local_baskets.append(m[:-5])
        settings.local_sounds.sort()
        settings.local_analysis.sort()
            
    
    def __init__(self):  
        self.scan_folder()
        self.autoSave = False
        try:
            temp = open('api_key.txt').read().splitlines()
            self.set_token(temp[0],"token")                      
        except IOError:
            api_key = raw_input("Enter your api key: ")
            temp = open('api_key.txt', 'w')
            temp.write(api_key)
            temp.close()
            print "Your api key as been stored in api_key.txt file"
            self.__init__()
            
    def my_text_search(self, **param):
        """
        Call text_search method from freesound.py and add all the defaults fields and page size parameters
        TODO : add default param more flexible (store in a param file - add the api_key in a .py file)
        
        >>> import manager
        >>> c = manager.Client()
        >>> result = c.my_text_search(query="wind")
        
        """
        
        results_pager = self.text_search(fields="id",page_size=150,**param)
        #self.text_search(fields="id,name,url,tags,description,type,previews,filesize,bitrate,bitdepth,duration,samplerate,username,comments,num_comments,analysis_frames",page_size=150,**param)
        return results_pager
        
        
    def my_get_sound(self,idToLoad):
        """
        Use this method to get a sound from local or freesound if not in local
        >>> sound = c.my_get_sound(id)
        """
        
        sound = self._load_sound_json(idToLoad)
        if not(sound):
            blockPrint()
            try:     
                sound = self.get_sound(idToLoad)
                if self.autoSave:
                    self._save_sound_json(sound) # save it
            except ValueError:
                print 'File does not exist'
            enablePrint()

        return sound
        
    def my_get_sounds(self,idsToLoad):
        """
        Use this method to get many sounds from local or freesound 
        """ 
        
        sounds = []
        nbSound = len(idsToLoad)
        Bar = ProgressBar(nbSound,LENGTH_BAR,'Loading sounds')
        Bar.update(0)
        for i in range(nbSound):        
            sounds.append(self.my_get_sound(idsToLoad[i]))  
            Bar.update(i+1)
            
        return sounds

    def my_get_analysis(self,idToLoad):
        """
        Use this method to get an analysis from local or freesound if needed
        
        >>> analysis = c.my_get_analysis(id)  
        """
        
        analysis = self._load_analysis_json(idToLoad)
        
        if not(analysis):
            sound = self.my_get_sound(idToLoad)
            blockPrint()
            try:
                analysis = sound.get_analysis_frames()
                if self.autoSave:
                    self._save_analysis_json(analysis, idToLoad)# save it
            except ValueError:
                print 'File does not exist'
            enablePrint()
                
        return analysis
          

    def my_get_analysiss(self,idsToLoad):
        """
        Use this method to get many analysis from local or freesound
        """
        
        analysis = []
        nbAnalysis = len(idsToLoad)
        Bar = ProgressBar(nbAnalysis,LENGTH_BAR,'Loading sounds')
        Bar.update(0)
        for i in range(nbAnalysis):
            analysis.append(self.my_get_analysis(idsToLoad[i]))  
            Bar.update(i+1)
            
        return analysis  
    
    
    def _save_sound_json(self,sound):
        """
        save a sound into a json file
        TODO : add overwrite option...
        """
        settings = SettingsSingleton()
        if sound and not(sound.id in settings.local_sounds):
            nameFile = 'sounds/' + str(sound.id) + '.json'
            with open(nameFile, 'w') as outfile:
                json.dump(sound.as_dict(), outfile)
            settings.local_sounds.append(int(sound.id))
            settings.local_sounds.sort()
    
    def _load_sound_json(self,idToLoad):
        """
        load a sound from local json
        """
        settings = SettingsSingleton()
        if idToLoad in settings.local_sounds:
            nameFile = 'sounds/' + str(idToLoad) + '.json'
            with open(nameFile) as infile:
                sound = freesound.Sound(json.load(infile),self)
            return sound
        else:
            return None
          
           
    def _save_analysis_json(self,analysis,idSound):
        """
        save an analysis into a json file
        TODO : add overwrite option...
        """
        settings = SettingsSingleton()
        if analysis and not(idSound in settings.local_analysis):
            nameFile = 'analysis/' + str(idSound) + '.json'
            with open(nameFile, 'w') as outfile:
                json.dump(analysis.as_dict(), outfile)
            settings.local_analysis.append(int(idSound))
            settings.local_analysis.sort()

    def _load_analysis_json(self,idToLoad):
        """
        load analysis from json
        """
        settings = SettingsSingleton()
        if idToLoad in settings.local_analysis:
            nameFile = 'analysis/' + str(idToLoad) + '.json'
            with open(nameFile) as infile:
                analysis = freesound.FreesoundObject(json.load(infile),self)
            return analysis
        else:
            return None

    def load_analysis_descriptor_json(self, idToLoad, descriptor):
        """
        load analysis frames of a descriptor
        TODO : add this function in the workflow, add class with possible descriptors
        """
        analysis = []
        settings = SettingsSingleton()
        if idToLoad in settings.local_analysis:
            nameFile = 'analysis/' + str(idToLoad) + '.json'
            with open(nameFile) as infile:
                parser = ijson.parse(infile)
                for prefix, type, value in parser:
                    if prefix == descriptor:
                        analysis.append(float(value))
            return analysis
        else:
            return None

# TODO : change the analysis and load only one type of analysis from the json, create classes
class Basket(Client):
    """
    A basket where sounds and analysis can be loaded
    >>> b = manager.Basket()
    TODO : save baskets, create library of baskets, comments, title, ...
    """
    
    def __init__(self):
        self.sounds = []
        self.analysis = []
        self.ids = []
        Client.__init__(self)
    
    def push(self,sound=None,analysis=None):
        """
        >>> sound = c.my_get_sound(query='wind')
        >>> b.push(sound)
        
        """
        self.sounds.append(sound)
        self.ids.append(sound.id)
        self.analysis.append(analysis)

    def update_sounds(self):
        nbSound = len(self.ids)
        Bar = ProgressBar(nbSound, LENGTH_BAR, 'Loading sounds')
        Bar.update(0)
        for i in range(nbSound):
            if not(self.sounds[i]):
                self.sounds[i] = self.my_get_sound(self.ids[i])
            Bar.update(i + 1)

    def update_analysis(self):
        """
        Use this method to update the analysis.
        All the analysis of the sounds that are loaded will be loaded
        
        >>> results_pager = c.my_text_search(query='wind')
        >>> b.load_sounds(results_pager) 
        >>> b.update_analysis()
        
        """
        nbSound = len(self.analysis)
        Bar = ProgressBar(nbSound,LENGTH_BAR,'Loading analysis')
        Bar.update(0)
        for i in range(nbSound):
            if not(self.analysis[i]):
                self.analysis[i] = self.my_get_analysis(self.ids[i])
            Bar.update(i+1)
        
    
    def load_sounds(self, results_pager):
        """
        Use this method to load all the sounds from a result pager int the basket 
        this method does not take the objects from the pager but usgin my_get_sound() which return a sound with all the fields
        
        >>> results_pager = c.my_text_search(query='wind')
        >>> b.load_sounds(results_pager)

        """
        nbSound = results_pager.count
        numSound = 0 # for iteration
        results_pager_last = results_pager             
        Bar = ProgressBar(nbSound,LENGTH_BAR,'Loading sounds')
        Bar.update(0)
        # 1st iteration                              # maybe there is a better way to iterate through pages...
        for i in results_pager:
            self.push(self.my_get_sound(i.id))
            numSound = numSound+1
            Bar.update(numSound+1)
            
        # next iteration
        while (numSound<nbSound):
            blockPrint()
            results_pager = results_pager_last.next_page()
            enablePrint()    
            for i in results_pager:
                self.push(self.my_get_sound(i.id))
                numSound = numSound+1
                Bar.update(numSound+1)
            results_pager_last = results_pager


    def save(self,name):
        """
        Use this method to save a basket
        """
        settings = SettingsSingleton()
        if name and not (name in settings.local_baskets):
            nameFile = 'baskets/' + name + '.json'
            with open(nameFile, 'w') as outfile:
                json.dump(self.ids, outfile)
            settings.local_baskets.append(name)
            nbSound = len(self.ids)
            Bar = ProgressBar(nbSound, LENGTH_BAR, 'Loading sounds')
            Bar.update(0)
            for i in range(nbSound):
                Client._save_sound_json(self, self.sounds[i])
                Client._save_analysis_json(self, self.analysis[i],self.ids[i])
        else:
            print 'give a name that does not exist to your basket'

    def load(self,name):
        """
        Use thise method to load a basket
        """
        settings = SettingsSingleton()
        if name and name in settings.local_baskets:
            nameFile = 'baskets/' + name + '.json'
            with open(nameFile) as infile:
                self.ids = json.load(infile)
        nbSound = len(self.ids)
        self.sounds = [None] * nbSound
        self.analysis = [None] * nbSound
        self.update_sounds()
        print ''
        self.update_analysis()


    # TO RENOVE
    def load_sounds_pager(self, results_pager):
        """
        Use this method to load all the sounds from a result pager in the basket (this method takes sounds from the pager - WARNING : fields will be the one asked in the request for the pager...) TODO : probably remove this function...
        
        >>> results_pager = c.my_text_search(query='wind')
        >>> b.load_sounds_pager(results_pager)
        
        """
        
        def load_sound(sound):
            sound.name = strip_non_ascii(sound.name)
            #self.__save_sound_json(sound) # save sound
            self.push(sound)
        
        nbSound = results_pager.count
        numSound = 0 # for iteration
        results_pager_last = results_pager
        Bar = ProgressBar(nbSound,LENGTH_BAR,'Loading sounds')
           
        # 1st iteration
        for i in results_pager:
            load_sound(copy.copy(i))
            numSound = numSound+1
            Bar.update(numSound+1)
            
        # next iteration
        while (numSound<nbSound):
            blockPrint()
            results_pager = results_pager_last.next_page()
            enablePrint()    
            for i in results_pager:
                load_sound(copy.copy(i))
                numSound = numSound+1
                Bar.update(numSound+1)
            results_pager_last = results_pager
            #print ' \n CHANGE PAGE \n '


    # REMOVE THIS AND ALLOW TO SAVE A BASKET IN A FOLDER (save ids only and query request and some comments...)
    def save_sounds_json(self):
        """
        WARNING : does not work because it calls a private method from Client __save_sound_json
        However, this method is useless since we save all the sounds we get from the method my_get_sound()
        Use this method to save all loaded sounds in the basket into json files
        """
        
        if not os.path.exists('sounds'):
            os.makedirs('sounds')
       
        numSound = 0
        nbSound = len(self.sounds)
        
        Bar = ProgressBar(nbSound,LENGTH_BAR,'Saving sounds')
        
        while (numSound<nbSound):
            Client.__save_sound_json(self.sounds[numSound])
            numSound = numSound+1
            Bar.update(numSound+1)

    
# TODO :    create a class for utilities
#           add management of baskets
#           add a class for (sound analysis id)
#           
#_________________________________________________________________#
#                             UTILS                               #
#_________________________________________________________________#
class ProgressBar:
    '''
    Progress bar
    '''
    def __init__ (self, valmax, maxbar, title):
        if valmax == 0:  valmax = 1
        if maxbar > 200: maxbar = 200
        self.valmax = valmax
        self.maxbar = maxbar
        self.title  = title
    
    def update(self, val):
        import sys
        # format
        if val > self.valmax: val = self.valmax
        
        # process
        perc  = round((float(val) / float(self.valmax)) * 100)
        scale = 100.0 / float(self.maxbar)
        bar   = int(perc / scale)
  
        # render 
        out = '\r %20s [%s%s] %3d / %3d' % (self.title, '=' * bar, ' ' * (self.maxbar - bar), val, self.valmax)
        sys.stdout.write(out)
        sys.stdout.flush()
        
# disable logging         
import sys, os
# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')
# Restore
def enablePrint():
    sys.stdout = sys.__stdout__


# Needed to remove non asci caracter in names
def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)







#propably garbadge
#    def save_analysis_json(self):
#        """
#        Use this method to save previoulsy loaded analysis to json files (name:sound_id)
#        Care : if the loaded sounds are not corresponding with the loaded analysis, wrong name will be given to json files...
#        
#        TODO : fix it to remove the care problem...
#        """
#        
#        if not os.path.exists('analysis'):
#            os.makedirs('analysis')
#         
#        numSound = 0
#        nbSound = len(self.loaded_sounds)
#        
#        Bar = ProgressBar(nbSound,LENGTH_BAR,'Saving analysis')
#        
#        while (numSound<nbSound):
#            nameFile = 'analysis/' + str(self.loaded_sounds[numSound].id) + '.json'
#            if self.loaded_analysis[numSound] and not(os.path.isfile(nameFile)):
#                with open(nameFile, 'w') as outfile:
#                    json.dump(self.loaded_analysis[numSound].as_dict(), outfile)
#            numSound = numSound+1
#            Bar.update(numSound+1)
#        
#    def load_analysis_json(self,idToLoad):
#        """
#        Use this method to load all analysis in a FreesoundObject from all json files
#        idToLoad : list of sound id or 'all'
#        
#        """
#         
#        if (idToLoad == 'all'):
#            files = os.listdir('./analysis/')
#            nbSound = len(files)
#            Bar = ProgressBar(nbSound,LENGTH_BAR,'Loading analysis')
#            self.loaded_analysis = [None]*nbSound
#
#            for numSound in range(nbSound):
#                with open('analysis/'+files[numSound]) as infile:
#                    self.loaded_analysis[numSound] = freesound.FreesoundObject(json.load(infile),self)
#                Bar.update(numSound+1)
#            
#        else:    
#            nbSound = len(idToLoad)
#            Bar = ProgressBar(nbSound,LENGTH_BAR,'Loading analysis')
#            self.loaded_analysis = [None]*nbSound
#            for numSound in range(nbSound):
#                with open('analysis/'+str(idToLoad[numSound])+'.json' ) as infile:
#                    self.loaded_analysis[numSound] = freesound.FreesoundObject(json.load(infile),self)
#                Bar.update(numSound+1)
#            
#    def load_sounds_json(self,idsToLoad):
#        """ 
#        Use this method to load sounds from all json files
#        TODO : add param to load only certain sounds
#        ADD A GENERAL JSON WHERE ALL TITLES/TAGS/ID ARE IN ORDER TO BE ABLE TO SEARCH TEXT, ...
#        """
#        
#        if (idsToLoad == 'all') :
#            files = os.listdir('./sounds/')
#            nbSound = len(files)
#            Bar = ProgressBar(nbSound,LENGTH_BAR,'Loading sounds')
#            self.sounds = [None]*nbSound
#            for numSound in range(nbSound):
#                with open('sounds/'+files[numSound]) as infile:
#                    self.sounds[numSound] = freesound.Sound(json.load(infile),self)
#                Bar.update(numSound+1)
#        else:
#            nbSound = len(idsToLoad)
#            Bar = ProgressBar(nbSound,LENGTH_BAR,'Loading sounds')
#            self.sounds = [None]*nbSound
#            for numSound in range(nbSound):
#                with open('sounds/'+str(idsToLoad[numSound])+'.json') as infile:
#                    self.sounds[numSound] = freesound.Sound(json.load(infile),self)
#                Bar.update(numSound+1)
#                
#      
#

#   
#    def save_json(self):
#        self.save_sounds_json()
#        self.save_analysis_json()
#            
#    def load_json(self, idToLoad):
#        self.load_sounds_json(idToLoad)
#        self.load_analysis_json(idToLoad)
