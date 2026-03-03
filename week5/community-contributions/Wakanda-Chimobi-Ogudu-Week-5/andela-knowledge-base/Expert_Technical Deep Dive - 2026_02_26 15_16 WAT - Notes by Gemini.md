Feb 26, 2026

## Expert/Technical Deep Dive \- Transcript

### 00:00:00

   
**Zion Pibowei:** All right. Um, where is everybody? I can see just a few persons on the call yet. Um, good morning, good afternoon, good evening, depending on where you're joining from. Uh, I hope you guys are having a really swell day. Um, if you guys are on this call, I would like to see some thumbs up and some emojis. Let's know how active the call is. All right. All right. And how is your week one going? so far. Um I believe that you guys have um been gradually coming up to speed and um um I know there's still a few challenges or issues that some of you have been facing here and there. Um and we've been on top of everything just to make sure that you guys have a very smooth um start to the program and kudos on all the progress you guys have made so far. For those of you who have made some really good progress um especially with the learning material today we are going to be going further.  
   
 

### 00:01:32

   
**Zion Pibowei:** We are actually going to be having um a workshop this afternoon um where we are going to be looking into a very important topic for building AI applications. Um I just want a few more persons to join us before we actually kick off the the topic for today the agenda for today. So, I'm going to drop a poll. Um, I want to know the progress of you guys in week one. So, I'm going to drop a poll now to to know So one second. Yeah. Hopefully before the pool is over everyone would have been on the call. So, um I would be I would be dropping this poll now. So, please check the poll that I just dropped and I believe week this is week four in the Udemy course. So, it's our day four for this week. So, if you've gotten here, I would like to know. I would like to know. So, please vote on the poll. according to the top showdown evaluating models for code gen and business task is day four current week one but course it is um section four week four so if you've gotten here let me know I want to know how far you guys have come um if you already started it I want to  
   
 

### 00:04:26

   
**Zion Pibowei:** to the numbers take progress. So whether you have completed it on so far people on this great I'm going to share my screen to see your votes on this poll. Let me see how far we've come. So, this is 46 volts. Um, I hope nobody's having trouble check. Go. So, have you got to know if you've crossed it? So if you've crossed it very What's going on, guys? install.  
**umar Javed:** Um, Zen, you're not properly audible. Your voice is breaking. Uh, I mean, it's it's been from the last 5  
**Zion Pibowei:** Okay.  
**umar Javed:** minutes.  
**Zion Pibowei:** Okay. So, that was that was a problem, right? So, let me quickly adjust that. Okay, I think I know why that was happening. Just give me a second, guys. Um, so is it is it is it better now? I think I just switched to my internet.  
**umar Javed:** Yeah, it's better now.  
**emmy wonder:** Yeah,  
**Zion Pibowei:** So, let me know now, guys.  
   
 

### 00:07:41

   
**emmy wonder:** it's fantastic.  
**Zion Pibowei:** Okay. All right. So, um I I hope that was the the issue that some of you are having because I saw a lot of sad emojis and I was wondering what was going on. All right. So, let's um let's hope that that was it. Um, now my camera is not coming up. One second.  
**umar Javed:** I think he has some internet issues. Let's just give him a minute. Let's wait for him.  
**Abdul:** Can someone follow up with Zion?  
**umar Javed:** I think we can uh post it our channel. Give me a second. Let me do it.  
**Zion Pibowei:** Really sorry guys, a lot of um technical glitch this this morning, this afternoon. Really sorry. Also seem to be having some issues with camera here. But yeah, let's let's just hope it it comes up. I would not let that be a blocker any further. So I'll just go ahead and we'll get started. Um for the poll I dropped earlier, let's look at that.  
   
 

### 00:16:33

   
**Zion Pibowei:** Um 64 votes. Yeah. So again, if you've not dropped your vote, just go to the poll, let me know where you guys are in the topic um in the in the learning outline for today. But I will just proceed to share my screen. Um so today we're going to be looking at we're going to be having a a a an interesting exploration of data embeddings. Um, and we're about to start um or go deeper into RAG. And so it's essential that we take a careful look at what this really is. What makes vector impedance really important? What are vector embeddings anyways? So we're going to be looking at this um today. So very quickly before I start, I want to um I'll launch a Q\&A. So I want you guys to tell me in your current understanding in your current understanding what do you understand by a vector embedding right so please use the Q\&A feature um I think I'll be putting this up so what do you guys understand by vector embeddings I want you guys to drop your comments there and and please I hope everyone can hear Okay, because it looks like my internet is just really messy today.  
   
 

### 00:18:01

   
**Zion Pibowei:** So, what do you understand by vector embeddings? So, I'm dropping this in the Q\&A. So, please just use the Q\&A um button um as though you want to ask a question, but use that to um drop what you understand. Right? So um in one or two lines, what do you understand by vector embeddings? I might have to switch my camera to the traditional one. What do you understand by vector embeddings? So while you guys are pondering over that, I'll just get right into it. Um so today we'll just look at some things. We're going to look at very practically um what this is. So get ready to to write some code and we're going to play around with a a Google collab which I developed for this topic. All right. Um so I want to start I like to start with a little bit of motivation because usually or often when you hear the tempance it's like you know there's just a deep dive into the mathematical aspect of it.  
   
 

### 00:19:27

   
**Zion Pibowei:** So you know we start to talk about numbers and um semantic semantic representations and things like that. But let's start with a very interesting um introduction or motivation and let's use Spotify. Now, how many of you just drop some emojis if you're in this category? How many of you listen to music um with Spotify? You listen to music with Spotify, right? And so, um everybody, so pretty much everybody. And you know there was a time some 10 plus years ago um and when people started when when the when the feature Spotify discover um discover weekly dropped it was amazing to a lot of people right um it was like the feature understood the listeners very carefully understood what genre of music they were interested in understood how to make very carefully crafted recommendation Right. Of course, since the last 10 years, um, a lot of people have kind of gotten used to recommendation algorithms. Um, but a lot of people don't necessarily understand what it means or what what really happens under the hood, right?  
   
 

### 00:20:41

   
**Zion Pibowei:** And so, it is this thing that happens under the hood that we're about to explore in this session. Um, so what Spotify really um solves is a problem of choice. All right. So in a multitude of options and data and so many decisions to make, Spotify helps you streamline that choice, right? So one quick example I like to give when it comes to streamlining choices is that you know many times we always say that we need data to make decisions and people always think that when they have data they can make good decisions, right? But there's a choice overload that comes when you have an abundance of data to make decisions with. So many of you have gone to restaurants and um you've requested for for the menu and then when the menu arrives you realize that you are completely um you are completely confused as to what to order. How many of you have had that experience? You were thinking that when they brought the menu to you to streamline what you want to order or you would be interested in some specific ones, but then you see a multitude of choices, you would like to purchase every one of them, but you just don't have that luxury to to buy everything or to even eat everything.  
   
 

### 00:21:52

   
**Zion Pibowei:** All right? And you realize that you are actually confused. So, I mean, I've been in such instances or in such cases where I didn't have to ask the um the the waiter or wherever it is that I'm speaking with to tell me their best seller because I'm so confused about the the options in the menu that I really do not know what to pick and at this point I really just need guidance on, you know, what to go for. And so we always think that having a multitude of options helps us to make better decisions. But what really happens essentially is that a multitude of options just makes us um overburdened and we have this choice overload and so that's where recommendation algorithms come in. So think of your the waiter in the restaurant as the recommend recommener system. that when you become overloaded with multitude of choices, the the recommended system then tells you, okay, let us streamline your choice to this and this and this. All right? So that way the waiter just tells you three very good options that you can go for and then you pick one out of those three.  
   
 

### 00:23:12

   
**Zion Pibowei:** All right? Or the waiter can go further and just give you the very specific recommendation that is very suited for your need at that moment. That is what recommendation algorithms do. Now we are used to recommendation algorithms across multiple um interactions in social media whether you are on on on Instagram or on Tik Tok or on YouTube right um you what you see is recommendation algorithms right even when you browse even when you um are doing a Google search a recommendation algorithm is is is powering your search all right and what it essentially does is to be or create a compass for you all Right. So now for you to understand what really happens under the hood and we're going to play around this with data. So at the end of this session we are all going to be able to generate this cluster um and understand what the clusters mean. But let's start with a simple cluster. Um this is an easy cluster. Essentially, we have played around here with some some um Spotify songs, millions of Spotify songs, right?  
   
 

### 00:24:17

   
**Zion Pibowei:** And what we have used to generate this diagram or this cluster that you see here is the TSN algorithm. All right. And so the TSN algorithm is the T distributed stoastic neighbor embedding algorithm. Don't worry if that's um that term sounds like a tongue twister. I promise you it's not meant to twist your tongue. All right, it is a nearest neighbor algorithm for sure. um but is the algorithm that powers um it's one of the underlying algorithms or the key algorithm that powers Spotify um recommener system and what this algorithm does is that it helps you generate what we call vectors right which we are still going to look at what vectors are and I'm building this up carefully so that you guys start from um a visual example that you can relate to before we get to the core of these um um vector to embed it. So how do we generate this kind of data set? I'm going to drop the steps for you guys. Um and we are going to actually demonstrate this in Google Collab.  
   
 

### 00:25:24

   
**Zion Pibowei:** So um I'm dropping the link in the chat. So please head over to um head over here to download the Spotify data set. I'm going to go over your every everybody's responses for those who answered my question earlier. So, but I want you guys to download this Spotify data set because we're actually going to demonstrate this very shortly. So, the next thing I want you guys to do is to come to this collab. Um, I need to share the link with everyone. So, we're going to use this collab link here. Um, okay. So, I need to I need to open this collab so everybody can view and download. Um, give me one second. So I need you guys to check if you can access this link. So this is a collab. So check um if you can access the collab link. So I've dropped I've dropped a data set link but I've also dropped a link to the Google collab. Um let's see if you guys are able to find it.  
   
 

### 00:27:36

   
**umar Javed:** And I think the collab file is restricted.  
**Zion Pibowei:** Um okay one second. I'm actually just saying that um I think where I save this collab is a bit restricted in the sense of giving general access to everyone. Um don't worry guys let me I'll drop another link. Don't don't don't share a request. Don't send a request. I'll just drop a I'll drop a copy for this so that everybody can access it. Um, good. So, I'm dropping. So, this is the working version. So, I'm dropping this here. So, check this link again and see if you can access it. So, this is what we're going to be using for um the demonstration today. So feel free to download it from there or to make a copy in your own drive so that you're able to um to run it. Um I think for this one I just made everyone a viewer. So you would have to probably um copy in your drive so you can run it.  
   
 

### 00:28:52

   
**Zion Pibowei:** So we're going to just go over it step by step right and by the end of the session you should see how it works. So download the Spotify data set. That's step one. Then load the data into a pandas data frame. We're going to get there. um then select specific numerical features that quantify different audio attributes because we're going to look at different audio attributes. Then we're going to apply the TSN algorithm. Remember the TSN is the T distributed stoastic nearest neighbor algorithm. Um and we use this to learn the embeddings from these audio features. Then we plot the clusters of similar music. Up until now I've not given you a definition for a vector of an embedding. So, we're going to get there. Let's just take a step by step, right? Um, yeah. So, let's let's get right into it. So, I'm going to reshare my screen and we'll go to the collab. Um, have you guys been able to access the notebook now?  
   
 

### 00:29:51

   
**Zion Pibowei:** And are you guys ready to code along with me? All right. Awesome. So, very shortly I will share my screen. um to present something else. So, we're going to sharing this. So, let me know when you can see this. I'm just going to just get right into it. So what I want you guys to do is that once you download the data set which I believe many of you have already just um drag the data into this. So what you do is that you come here to the left panel and you go to this folder icon. I hope you guys can see it. So there's a folder icon here. All right. So come right here, open it and then just drag your data into this place. So we'll be able to just access it directly from here. All right. Um, yeah. So, let's do that. So, start by installing these three libraries. This will be the major the four libraries.  
   
 

### 00:31:06

   
**Zion Pibowei:** Sorry. So, these are the four packets we're going to be using in this session. Um, so again, you know, these are like traditional ML frameworks that we're using for this session. Um, okay. I can see some thumbs down. What are we thumbs down? What are we putting a thumbs down too.  
**emmy wonder:** I think some of them are not properly set properly.  
**Zion Pibowei:** Okay. Should I should I hold on like a few seconds? Okay. So, step one, download the data set which I've dropped in the chat. Step two, download the collab notebook which I have also dropped in the chat. and then um I'll wait for 30 seconds so you guys can just get set for that. All right, while we're waiting for that, I want to maximize the time. So, let's go into the poll. I have a half stop in the next 30 minutes. So, I will really try as much as possible to wrap up by then. So, we're not going to be use our full 90 minutes in this session.  
   
 

### 00:32:16

   
**Zion Pibowei:** Um so the other time I was asking you guys to tell me what vectors and vector embeddings are. So science says steps to numerical vector conversion such a way similar meaning what correspond corresponding vectors come closer. Okay that's good. Um they quantify various aspects of the tokens and their relationships. This is Rywick. Then Wuka says vector embeddings are numerical representations of documents stored in vector databases. So yeah, numerical representations of documents and we store them in a vector database. But what happens if you store your vectors in an Excel sheet? Does it stop being a vector? Um, okay. No reading says embedding is a vector representation of words which are then used to group words or sentences closer in meaning to each other. Okay, that's a good one too. I mean you guys are have are given some really interesting um definitions which which make a lot of sense. It is representation of data in a way easy for machine understanding. That also is a good one.  
   
 

### 00:33:21

   
**Zion Pibowei:** Um that's a very good one as well. Um mathematical representations of data numerical representations of data embedded are vectors that locates a token in the vector space. Okay. So, yeah. So, you guys have really given interesting definitions. Many of you have an idea of what this really is. And so, it's it's good to see um it's it's good to see, right? And so, can we proceed now? Are you guys um are you guys set? Science says there are 84 codes. Which should I download? So, I believe you're referring to the Spotify link. Just download the one that says Spotify features CSV. That's the one we're interested in.  
**emmy wonder:** Zion, can you just please quickly go through where they should um the folder they should put it on again?  
**Zion Pibowei:** Yeah, I would actually go back there. But as long as um the other question around the downloading is is very clear. Um okay, please confirm that you you've gotten the right one to download.  
   
 

### 00:34:39

   
**Zion Pibowei:** Just do a thumbs up. Let me see. Perfect. All right. Um so let's now come back to the notebook collab. Um and we are going to we are going to um start. So, oh the the the video is the camera is now back up. So, let me just turn it on. Yeah, sorry guys for that. Just my camera acting up. So, now we come to um the Spotify data set. So, what I want you guys to do is to come here. All right. So once you've launched the collab and you are right on this interface, you are on your own version of Google Collab. What you do is that you come here to um this folder icon on the left panel. Drag your Spotify data set here, right? Um I believe you can also upload using this button, but you can do drag and drop. It's it's perfectly fine if you do that. Now once that is uploaded, then you are good to go.  
   
 

### 00:35:50

   
**Zion Pibowei:** Uh so you can just go ahead to install these packages. So we install these packages because these are the things that we're going to use. So these are traditional lemon packages. Those of you that have done data science or come from a data science or data background in general, we're very familiar with pandas, scikitlearn, mplot live and seaborn. So pandas is usually a tool for data manipulation, right? Scikitlearn is a tool for machine learning. So this is what we're going to use to learn the embeddings. So remember we are learning the embeddings which means that we're trying to learn a model and the way we learn models is by running an algorithm on data. So we run an algorithm on data to learn a model. In this case the algorithm we are running on the data is the tsn algorithm right the end result of that algorithm is um is the embedding that is the end result of that algorithm run on the data is embedding. So scikit learn is a package that allows us to learn that.  
   
 

### 00:36:48

   
**Zion Pibowei:** Then map is a visualization library that allows us to visualize the embeddings. Um corn also helps us to aid the um the algorithm choice um that we are going to use for the learning. Right? So the next thing you are running these imports. So we're importing panda circuit learn map live. We're importing time. So as we measured how long it takes to learn the embeddings or to run the algorithms um for different sizes of data, right? Um remember the larger your data set, the longer it takes to run the algorithm on the data. So that's something very key I want you guys to take note of. Um and you guys can always play around with um with this in your own time. Um you can you can just play around with different um parameters and tune it in the way you want it and see how it works. All right. So with this data set in our um in our path we are going to just run this code now this cell.  
   
 

### 00:37:46

   
**Zion Pibowei:** So we um read the CSV into a data frame. So at this point we can um you can visualize what the data what the data frame looks like. So first off there's 232,725 rows in this data frame. So essentially this Spotify data set has 232, 700 plus samples of music. That's what it means. It means that you have 200,000 plus samples of music in this data set. All right. Now what we do is that we are not trying to right now we we we don't want to run the algorithm on 200,000 samples. That that's just a lot and it's going to take time. So what do we do? we subsample the data set randomly. So we do a random subsampling of the data set where we sub where we where we randomly sample 20,000 um um samples from the original 200,000. The reason we do it randomly is just so that there's representation from different um categories of music in the smaller subset of the sample that we're trying to draw.  
   
 

### 00:38:57

   
**Zion Pibowei:** Right? So we draw the sample. We we we label this as DF subsets. Um and then let's let's look at what the table looks like. So this is what it looks like essentially for for those who are not familiar with this um um what we've just done now it's we've taken the data frame which is the original table of 20,000 samples that we just drew here and now we are saying show me the first five rows all right of this uh new data set. So that's what df\_ subset head does. And so it returns the the um first five samples in the data set. And now we can see the different attributes of this data. It has genre, it has artist name, it has track name, that's track ID, that's popularity and so on down to um time signature and valance. Right? We have features like loudness. So pretty much we have all the necessary acoustic features, music features that are necessary to use in order to mathematically um represent the interests of the listener and sort of group what the listeners will be interested in based on different features.  
   
 

### 00:40:12

   
**Zion Pibowei:** Right? So these are the different music attributes that we can use to learn and embedding. Um now if you if you run this df subset of columns it just shows you a list of the columns that um are in this data set. So essentially there are um if you count this there's um there's 18 features right so we have 18 features here um which we can of course just do the math by running the len function. So it shows that 18 features in this in this data. Anyways, um we we we are not interested in using all the features. We want to just use very specific features. So what do we do? We create a new um a new list of the specific features that we're interested in. So particularly for the embedding we're trying to learn, we're interested in the popularity. Um pretty much we're interested in all numerical features, right? So if you notice, there are different types of features in this in this in this data. So we have the categorical features, we have the non- numerical features.  
   
 

### 00:41:19

   
**Zion Pibowei:** Um we have um we have we have these different features but we have the numerical ones. We are interested in the numerical features because it's numerical features that we need to use in order to draw mathematical relationships. Right? Of course, it doesn't mean that we cannot use um other features like for example we could numerically encode the genre feature. Um since this is since this is a categorical variable, right? We have different categories. We can definitely numerical numerically encode them into numbers and use that to learn what we want to learn. But we're not really interested in those for now. We're interested primarily in the ones that are that are numerical immediately. All right. So popularity is a numerical feature. Acosticness is a numerical feature. In fact, it's a continuous feature. Um dability, how dable is this? Is this music on a scale of 0 to one? That is what this feature is. Um duration, energy, um instrumentalness, um livveness, loudness, speechiness, tempo, violence.  
   
 

### 00:42:26

   
**Zion Pibowei:** Right? So these are the specific features that we are interested in um for the embedding that we want to learn right and again these uh make up 11 numerical features. So 1 2 3 4 5 6 7 8 9 10 11\. So now it's time to start to should I use the term to start to cook the the data set right. So let us uh create train and test sets. So in machine learning um we would essentially take a data set whenever we want to want to run an algorithm on data to build models we take the data right and then we split it into train test sets. Um essentially before we split into train tests we um we want to look at what specific transformations we probably need to do before that split. Um and then sometimes it's wise, in fact often it's wise to not do the transformation before the splits. So it's good to just know what transformations you want to run but then we split the data set into train and test. Then we take the train set um and further split it into train and validation.  
   
 

### 00:43:37

   
**Zion Pibowei:** So at the end of the day you have three sets. You have train sets, validation set and the and the test set. So the test set is the hold out set. The reason it's called the hold out set is that we are not using that set for any sort of validation while building the the the model or while running the algorithm. We're only going to we're going to hold it out until the end and only unleash it in the final evaluation that we need to do um for our final selected model. Right? Um but in this case we are not trying to necessarily do a um a train test validation set. So that's not really the agenda for now. What we're interested in is just a train set and a test set. So we split um first by um the the feature columns that we have in mind. Um actually I don't even think in this one we really did any train tests per se. Um I didn't go that far into train and test.  
   
 

### 00:44:39

   
**Zion Pibowei:** What I really just did here was um we have all the columns that will be that will be used as impute features which are the ones I was actually going to train essentially still the train set but there's no test set here. Um then we have the output feature the predictive feature which um which you're going to find out later right. So we start by um labeling this as X. So that is we take the data set that contains this specific features only um and then we pass that into the variable X. All right. Um so if you run this now if you run this this is what that data set looks like that table looks like. So this is this is our X and usually when we use X in in context of of data science or ML X is just simply a representation of all the input features that we're interested in. Right? And so these are the features that we're interested in for the work we're trying to do. Now um very quickly before we run the rest of the code I want to just tell you what to expect here.  
   
 

### 00:45:50

   
**Zion Pibowei:** So the first thing we want to do is to apply the algorithm to this data um and measure the time it takes to run the algorith algorithm on this data. All right. So we are going to u take that algorithm. We're going to we're going to instantiate the tsn algorithm. All right. and we're going to use it to fit transform um this impute I mean this this x um table. All right, we call that x2d. So that's the first thing we're going to do, right? So then the next thing we're going to do when we when we feed this, we check we measure the time it takes to to run this. Actually, let me start running this now. Um and initially I'm I'm just running with 200 samples because I want to see the time it will take to do that. All right. um it will take some time and so we want to measure the number of seconds it takes. Remember that this subsample has 20,000 um rows and we want to you know just look at how long it takes to feed that.  
   
 

### 00:46:52

   
**Zion Pibowei:** Um so we're starting with 200 samples. We can visualize what 200 samples look like um and see um you know like what the clusters look like. Then we can start increasing the the size until we get to 20,000 and then we see what the cluster size look like. Obviously the bigger the um the samples you use to train or fit the algorithm the more the embeddings have been learned and um you will see a difference in the cluster structure. So in order to visualize what we do is that we take that um um transform data set which is this x\_2d and we um and we um so we want to map this we want to add these coordinates back to the data frame right so we add new rows new um new columns sorry to this df subset set which is this DF subsets and then we add um we add um we're actually going to break this down so that you guys can understand. So we we um we take all features up until this point which I'm going to show you from this data set what that looks like.  
   
 

### 00:48:14

   
**Zion Pibowei:** So I think to take a step by step so that there's no confusion because I want everyone to understand what is going on here. Let's completely run this um algorithm first. So pause here once this is done and we have um the initial fit then I'm going to show you what x\_2d looks like and then you will see how we're subsetting that into x and y. So X is going to be a um um um X is going to be a 2D representation of this initially large um um data that has like 11 features. Right now one thing I want to quickly point out while we're waiting for that to run and I don't know if anyone else is running that but I I want to mention something that happens in the course of generating these embeddings. One of those things is dimensionality reduction. So in in data science and machine learning there's a concept of dimensionality reduction that takes place when we are trying to learn embeddings and what that simply means is that when we take data that is originally complex and has like a multitude of features or attributes right by the time we are done learning the embeddings we have essentially um condensed that larger data set with so many features and attributes into um a smaller subspace right um and we have taken or extracted all the meaningful representations from that original data set and  
   
 

### 00:49:41

   
**Zion Pibowei:** condensed it into a smaller subspace. So your final embeddings can just be two dimensional right um and those two dimensional carry all the meaning that is or should I say carry the most important meaningful things that um were extracted from the original data set. That's one very important thing to take note of. Okay. Um, so I think I'll pause now while waiting for this to run. Um, I'm I'm not sure why it's taking long on collab. So if if I'm running this locally, it will typically take, you know, maybe less than 60 seconds for 200 samples. So um there variety of factors that can make it take longer on collab including even the kernel that's been used um to run this. Um yeah anyways any questions before I continue? Any questions so far? Does anyone have any questions? Does anyone have any questions dropped in the Q\&A? Okay. Um I can actually see a question here. How how does a TSN model works? So the TSN model um first of all it's not a model it's an algorithm right and it's an algorithm that helps you learn an embedding model.  
   
 

### 00:51:39

   
**Zion Pibowei:** Now the reason I'm distinguishing this is because many people use algorithm and model interchangeably. So if there's one take I want everyone of you to have from this session it is that an algorithm is a procedure or a process right a model is a result of that process. A model will typically be an object or an artifact. A model is like a product of a process. All right. So an algorithm is a process that you implement on a data set. All right. So that's why in machine learning we talk about the learning algorithms or the machine learning algorithms. They are all learning algorithms, right? The model is not learning anymore. A model is learned. So there are two types of model. The um the model that has not learned anything meaning that its parameters do not have numerical values yet. It's just a um a plain model, a skeletal model. So we can write the equation of a model as y \= mx \+ c and that is our model.  
   
 

### 00:52:39

   
**Zion Pibowei:** But when we begin to learn what is the value of the m and what is the value of the c right we can learn that when we run an algorithm through data. So the moment we are done learning from the data we can then um um um pass values to m and c. So we can say y \= 3x \+ 2.5. that is a model that has learned um from the data. Right? So the process of arriving at this model that has learned is um a learning algorithm. All right. So that's the first thing. Second thing is that the way the TSN works is that it works by first of all it's a dimensionality reducing um algorithm. Right? An algorithm for dimensionality reduction. So what it does is that it takes data in a highdimensional space and computes similarity between all the points or all the numbers within that space. So similarity with numbers across all the all the all the features. For example, this table the TSN algorithm will compute similarity across all these numbers right um you know um across all these features.  
   
 

### 00:53:44

   
**Zion Pibowei:** And then the next thing that it does is that when it's done calculating that similarity, it then maps that into a lower dimensional space. It could be three dimensions. That is instead of having these 11 features, we can have three, we can have two. In the case of what we've just done now, we've we've reduced it to two dimensions. So when we reduce it to two dimensions, it condenses all those similarity scores into just two dimensions. And then um there a couple of other technical things that happen under the hood such as um um um um the fitting process that use gradient descent and all those things. A lot of complex mathematical detail there. Um when that is all done and the the um the similarity scoring is optimal or or has been optimized then um the the algorithm is done learning. we have the embedding that we can then use subsequently. Right? So essentially what what has really happened here is that we instantiated the algorithm here. Instantiate means that we have not run it.  
   
 

### 00:54:50

   
**Zion Pibowei:** We just instantiated it by specifying the parameters to use to run the algorithm. Right? Um and then the moment we instantiated it, we then applied it on the data. So this process now is the learning process. This fit transform. So the first thing that happens is the fit. The fit is where the learning algorithm learns the data and builds the model. Now once the model has been built that learn model is applied on the original data to transform the data. Right? So we fit to learn the model. We transform to apply the learning on the data to create the the outcome. All right. So that's what happens here. Um and so once that is done we then have the the result. So in this case it took 280 seconds which is a long time but anyways what does it look like? It looks something like this. So it's an array. It's a two dimensional array of numbers.  
**Ransford Okpoti:** Hey.  
   
 

### 00:55:44

   
**Zion Pibowei:** Um yeah go  
**Ransford Okpoti:** Hi, Zion. So, um, somebody has the hand up for a while.  
**Zion Pibowei:** ahead.  
**Ransford Okpoti:** Maybe it's related to what you talked about. So, maybe you can, um,  
**Zion Pibowei:** Okay I once once I'm done with this notebook I I'll take anyone who has their hands raised.  
**Ransford Okpoti:** pick the question.  
**Zion Pibowei:** But guys, in the meantime,  
**Ransford Okpoti:** Okay.  
**Zion Pibowei:** you can just use the Q\&A so that we are able to maximize time. Um, so in the two dimensional structure here, essentially we've taken 11 features and and condensed it into two dimensions, right? This is what has happened here. So now we then subset um we then subset by taking um this this column here as our X. All right. So here you see from here to zero which is the um the zero index. So the zeroth index means that the first number in each of these in each of these lists that you see in this array. So essentially we are taking this vertical numbers here.  
   
 

### 00:56:40

   
**Zion Pibowei:** Then in the case of this for y we subset it by taking the second numbers in the array. Right? So once we do that um we can then plot x against y. um but we can plot it in the context of the original DF subset. So if you notice we are trying to add this array back to back into the DF subsets table which had all the features that we used previously right so that by the time we are trying to visualize X against Y we can visualize it in the context of the DF subset and then look at the different genres and things like that. So the question is what does that look like? um and then we find that out by the plot. All right, so this is what the plot looks like. So this is just 200 samples. The clusters seem to be far apart. I would like you guys to on your own time play around with this data. Um and try this. We then want this cell for 20,000 samples.  
   
 

### 00:57:37

   
**Zion Pibowei:** So try increasing the sample size um by by subsampling here the way no by subsampling it here. Um, one second. Um, where did we subsample to 200? I don't think I don't think I subsampled to 200, which is why it took long. So, it actually plotted the entire 20,000 samples. So, yeah, sorry guys. I was supposed to have done that here actually and done the 200 here. So, play around with this subsampling here. All right. reduce the numbers as as you as you would like. Increase it, reduce it, and see how long it takes. I was wondering why it was taking so long, not realizing that I was working with the original 20,000 samples I had um there. So, this is for 20,000. This is what the cluster looks like. Um essentially, what you can see in this plot is that um we can see the different we can see different samples within Jum within within a genre um together in the same strand, right?  
   
 

### 00:58:42

   
**Zion Pibowei:** Um I mean sorry we can see different u um samples from different genre um within within the same strand which show similarity you know across different genres but they are all just you know um in in a single thread. Then you can see um how they dissociate from other other threads or other slices. Right? You can clearly tell that music or songs in this particular thread will be definitely very very different from songs in this other side. Right? So the farther the the the clusters are from from themselves, the more distance you know um um the songs are. And so when recommendation is being given or provided to the listener, right? Suppose we started a particular song somewhere here. Most likely all the songs that be um recommended will be songs that are falling within this tread until we have exhausted this tread and then maybe just jumps to the next tread and it just continues like that. That's essentially what is happening and it has been um executed or implemented by a learning algorithm.  
   
 

### 00:59:51

   
**Zion Pibowei:** Right? So I want us quickly go back to the to the notebook. Um I actually want to just wrap that up very quickly because of time um because I need to jump on a different call. So let us quickly then look at other aspects of embedments. I want to I want to know whether you guys now from a from a programmatic and a a visual standpoint do you understand what is going on with what we just just demonstrated? Do you guys understand what is going on? All right. Um, so let's now look at what all this means. So the major thing going on here is that it's all about representation, right? We're representing complex things as points in the high dimensional space. So we're taking complex attributes of music, right? Making them into numbers, bringing them into high dimensional space. High dimensional space means that the data set has so many columns, so many attributes. Um, in the case of our original data set was 18 columns.  
   
 

### 01:00:47

   
**Zion Pibowei:** We streamlined it to 11 numerical columns and in the 11 numerical columns we ran the algorithm on it and then we condensed it to just two um two embedding dimensions. Right? So it enables us to quantify similarities and cover semantic relationships. So what is really going on is that um the numbers become meaningful representation of the original attributes and then closer the numbers are to themselves the more similar the songs are. That is really what is going on. Um, so embeddings are dense, lowdimensional vector representations of data where similar things are close together. I want you to take note of three things here. We're talking about a vector. A vector is just an array of numbers. In the collab, you saw that array, that two dimensional array I showed you guys, that is the vector. So when we were done running the TSN algorithm, the result that we had was a two-dimensional array. It's a vector. All right. Now when we say it is dense what is really happening is that the vector has fewer dimensions.  
   
 

### 01:01:48

   
**Zion Pibowei:** So that is we condensed 11 dimensions into just two. But not just that right because of the of the way it was condensed most of the entries in the in the new data now the two dimensional data now are non zero. Right? So the opposite of a dense vector is a sparse vector where we have a lot of zeros right in the in the vector space. But in this case of embeddings, embeddings are usually almost entirely non zero, right? Because they packed with numerical information. Now they're low dimensional in the sense that we have compressed an originally large data, originally high dimensional data into lower dimensions, but we are preserving essential patterns. All right, we're preserving essential patterns. It's kind of like how you're watching a movie on a two-dimensional screen, but your brain understands that you're watching a three-dimensional um scene. So, the the the actual scene that is taking place is threedimensional, but you're watching it on a flat screen. All right? And so you you have not we're not losing information because we have we have um we have mapped a three-dimensional um activity or scene into a two dimensional surface.  
   
 

### 01:03:03

   
**Zion Pibowei:** We have not really lost a lot of information. Obviously there are some movies that you have to watch that you actually have to watch in 3D which means that they they they provide um additional aid like maybe some special glasses to use to watch those 3D movies. But that that's just like you know every once in a while it's not something that happens all the time. So what is really happening with embeddings is that they condensed versions of larger data. Um now again key properties is that embeddings capture similarity. So and we I think we can see that from the visualization that we had um in the in the demonstration we just ran where similar music tend to cluster together to themselves. Similar songs even if they're songs across different genres. So the different colors represent different genres. We clearly see that these different genres, but we now know that this, you know, there are songs that share similarities with themselves. And so when the when when the individual is listening to these recommendations, it doesn't feel like the recommendation is off.  
   
 

### 01:04:05

   
**Zion Pibowei:** The listener can im immediately tell if the genre has changed, right? But he also knows that it is still in line with his interests um in in in in terms of what um what suits the mood at that moment or the atmosphere at that moment. So again embeddings encode semantic relationships and they make data usable for algorithms. Right? So um embeddings are learned through an optimization process. Um and the way the algorithm works just like every other machine learning algorithm is that it will start with random embeddings right and then during training the model begins to adjust the vectors um because there an objective function it needs to optimize either minimize or maximize in this case it needs to minimize the loss function right so there's an internal metric that is um that is um associated with that learning process that the the model or the algorithm needs to maximize So if the if the metric is um is an is an error metric, it needs to minimize the error. If the metric is an accurac accuracy type of metric, then it needs to maximize um the the objective function.  
   
 

### 01:05:15

   
**Zion Pibowei:** And so after multiple iterations, the algorithm converges and gets to a point when um it has maximally learned and no further training would improve its accuracy or its performance on that objective metric. So at that point, we can stop the learning process. Again, I've just described a pretty general machine learning process um even beyond just embeddings, right? And so, this is um where we will stop for today. I'm going to make this u PDF available. You guys already have the collab and um yeah, I think that was it. So, we will stop here. Any other questions? I think I've seen a couple questions. I will try to quickly answer some of them very shortly. If you guys have more questions, still drop them in the chat. um and we'll go over them gradually. Okay. So, um I've answered how TSN works. Where exactly are binding it to 20 samples? I'm not sure I understood that. How did you specify 200 samples?  
   
 

### 01:06:19

   
**Zion Pibowei:** So, um if you go back to the collab where we did the subsampling was where we specify 200 samples. Um, sorry for that mix up earlier where um um it was originally 20,000 and the the first cell was just jumping into 200\. So you need to go back to that previous cell and um adjust it to 200, right? Um what is Cabon used for? Seaborn, we were using Cabbond for the algorithm selection. So if you go to the cell, you would you'd see where we imported TSN. No, no, no. We imported SNS from Sabon. Um, okay. No, Sabon was not used for algorithm selection. Sabon was used for, let me take a look. Um, we use Sabon for what exactly? Um, we use Cab for the scatter plot actually. Um, Son does have some mathematical algorithms as well, but I think for this one we just use Current for the algorithm. Are data frames synonymous with data sources? No. Data frames are not synonymous with data sources.  
   
 

### 01:07:27

   
**Zion Pibowei:** You pretty much load your data source into a data frame, right? Um if you if you've done engineering on Spark, then you must be familiar with data frame from from Spark. As an engineer, you need to have data science skills. I covered this in the last session. um it is good if you have data science skills is a good to have. But depending on what you'll be working in, it's not a must have. So if you're not going to be working in a research um setting or a setting where you're trying to in an applied setting where you're trying to bring like research into engineering so you're trying to maybe you know implement research papers or implement some of the state-of-the-art techniques um and bring them into applications then not necessarily if you're working mostly on um on on um um apply AI integration um or scaling side of things that is if your goal is you know if your function is build a rack system build agents right um orchestrate um the systems um own the AI system um and different things then you don't necessarily need very thorough um data science skills or machine learning skills for you to do that as long as you're not doing anything that requires going under the hood of a model, right?  
   
 

### 01:08:57

   
**Zion Pibowei:** Maybe having to fine tune open source models or having to go thoroughly into um the algorithms. As long as you're not doing any of those things that are very very algorithm specific, you do not necessarily need machine learning skills. It's a good to have because it helps you build like it helps you kind of understand what is going on generally right with the model ecosystem but it's I think it's a must have mostly for those working in the research and applied research fields um and those still working within data science so you can be an AI engineer in the data science environment for example you could be an AI engineer in the data science um team so in that kind of environment it's good to have data science skills and what pract Practically what I mean by an AI engineer in a data science setting is that for example you could be in a data science team where as an AI engineer your your major function is things like building the pipelines and and the techniques or methodology for evaluation right or for model observability and things like that in that context now you need some data science skills because um in evas or in model obser observability.  
   
 

### 01:10:09

   
**Zion Pibowei:** You need to understand some statistical aspect of of data science, statistical aspects of evaluating models. Um, you need to understand some of those interior details. Um, that you'll typically not really be very concerned with in broad engineering, right? So, it depends on where you really are in the spectrum. If AI engineering is more focused on um on building and shipping features, right? um building the the AI system, building the the um um building and deploying the solutions and things like that. You are not necessarily um you are not necessarily obligated to know core machine learning. Generally for me um I still think when you have a time it is still good to read widely every once in a while just so that you can understand how we got to this point especially from the um historical development side of things. Um okay so what is that TSN function doing exactly? This was asked by Morgan Thomas. I want to confirm if I later in the course of my explanation if you if you have understood it.  
   
 

### 01:11:25

   
**Zion Pibowei:** So can you do a thumbs up if you understand what the TSNA function is doing exactly? Okay, perfect. Um TSN is generally slow. Yes, I forgot I was doing two 20,000 samples instead of 200\. What I understand is it is something like PCA. Yeah, it's very similar to PCA. PCA being principal component analysis. Um and PC is strictly for dimensionality reduction. And the difference between PC and TSN is that TSNA is not just a means to an end. Um so TSNA helps you arrive at the actual model and then you can use that to generate the embeddings, right? Um PC of course is still a dimensionality deduction process. Um and it kind of it's kind of similar to the example I gave about how you watch a 3D scene on a 2D surface, right? So that's what essentially what dimensionality reduction algorithms do. Um, okay. I don't think you're running. Okay. Okay. Okay. I'm struggling to figure out the difference between 200 samples and 20,000 samples.  
   
 

### 01:12:31

   
**Zion Pibowei:** So what you just do, just change the subsample that we did earlier to 200 and then run a cell that I wrote 200\. You can create new cells. You can choose different numbers that you want to select. You will see the difference in the time for training. But particularly when you visualize the cluster, you also see the difference. There's going to be a very major difference between the two. Right? All right. So, thank you all for your time. Um, I'll be wrapping up here. Apologies, I'm not able to take all the questions. Please, just in case I've not covered your question and it's a very very important question, go to the channel, tag me on the channel, right, with your question. If it's a very very important question that I've not yet covered in my explanation so far, um, please be free to tag me in the channel. So that'll be a wrap from here. Hope you guys enjoyed the session. I guess we'll find out tomorrow during your debrief with um your your TAS.  
   
 

### 01:13:20

   
**Zion Pibowei:** So hope Rasport you guys should let me know how it went. Probably there are some persons who have not gotten a hang of it. But hopefully when you guys play around with the with the notebook, it will make a lot of sense and we'll be able to see what the progress looks like. I hope it has been an exciting week one for you guys. Um it's it's only going to get more interesting. Ed will be coming around um next week in in our week two deep dive. So you're going to see more ahead. I would I would take the back seat for most of the sessions next week and just be observing um maybe just being in the background to answer questions. But um I hope to see you um next week. Um I think the next time I'm seeing you guys is Tuesday. So this will be um a wrap for me this week for you guys. Enjoy the rest of your day uh and of your weekend and see you next week. So bye guys.  
   
 

### Transcription ended after 01:14:13

*This editable transcript was computer generated and might contain errors. People can also change the text after it was created.*