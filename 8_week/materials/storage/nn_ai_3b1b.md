 Neural networks
3Blue1Brown ·
Course
9 videos

---------

But what is a neural network? | Deep learning chapter 1

Timeline: 
0:00 - Introduction example
1:07 - Series preview
2:42 - What are neurons?
3:35 - Introducing layers
5:31 - Why layers?
8:38 - Edge detection example
11:34 - Counting weights and biases
12:30 - How learning relates
13:26 - Notation and linear algebra
15:17 - Recap
16:27 - Some final words
17:03 - ReLU vs Sigmoid


Introduction example
0:04
This is a 3.
0:06
It's sloppily written and rendered at an extremely low resolution of 28x28 pixels,
0:10
but your brain has no trouble recognizing it as a 3.
0:14
And I want you to take a moment to appreciate how
0:16
crazy it is that brains can do this so effortlessly.
0:19
I mean, this, this and this are also recognizable as 3s,
0:22
even though the specific values of each pixel is very different from one
0:27
image to the next.
0:28
The particular light-sensitive cells in your eye that are firing when you
0:32
see this 3 are very different from the ones firing when you see this 3.
0:37
But something in that crazy-smart visual cortex of yours resolves these as representing
0:42
the same idea, while at the same time recognizing other images as their own distinct
0:47
ideas.
0:49
But if I told you, hey, sit down and write for me a program that takes in a grid of
0:54
28x28 pixels like this and outputs a single number between 0 and 10,
0:59
telling you what it thinks the digit is, well the task goes from comically trivial to
1:04
dauntingly difficult.
Series preview
1:07
Unless you've been living under a rock, I think I hardly need to motivate the relevance
1:10
and importance of machine learning and neural networks to the present and to the future.
1:15
But what I want to do here is show you what a neural network actually is,
1:18
assuming no background, and to help visualize what it's doing,
1:22
not as a buzzword but as a piece of math.
1:25
My hope is that you come away feeling like the structure itself is motivated,
1:28
and to feel like you know what it means when you read,
1:31
or you hear about a neural network quote-unquote learning.
1:35
This video is just going to be devoted to the structure component of that,
1:38
and the following one is going to tackle learning.
1:40
What we're going to do is put together a neural
1:43
network that can learn to recognize handwritten digits.
1:49
This is a somewhat classic example for introducing the topic,
1:52
and I'm happy to stick with the status quo here,
1:54
because at the end of the two videos I want to point you to a couple good
1:57
resources where you can learn more, and where you can download the code that
2:00
does this and play with it on your own computer.
2:05
There are many many variants of neural networks,
2:07
and in recent years there's been sort of a boom in research towards these variants,
2:12
but in these two introductory videos you and I are just going to look at the simplest
2:16
plain vanilla form with no added frills.
2:19
This is kind of a necessary prerequisite for understanding any of the more powerful
2:23
modern variants, and trust me it still has plenty of complexity for us to wrap our minds
2:28
around.
2:29
But even in this simplest form it can learn to recognize handwritten digits,
2:33
which is a pretty cool thing for a computer to be able to do.
2:37
And at the same time you'll see how it does fall
2:39
short of a couple hopes that we might have for it.
What are neurons?
2:43
As the name suggests neural networks are inspired by the brain, but let's break that down.
2:48
What are the neurons, and in what sense are they linked together?
2:52
Right now when I say neuron all I want you to think about is a thing that holds a number,
2:58
specifically a number between 0 and 1.
3:00
It's really not more than that.
3:03
For example the network starts with a bunch of neurons corresponding to
3:08
each of the 28x28 pixels of the input image, which is 784 neurons in total.
3:14
Each one of these holds a number that represents the grayscale value of the
3:19
corresponding pixel, ranging from 0 for black pixels up to 1 for white pixels.
3:25
This number inside the neuron is called its activation,
3:28
and the image you might have in mind here is that each neuron is lit up when its
3:32
activation is a high number.
Introducing layers
3:36
So all of these 784 neurons make up the first layer of our network.
3:46
Now jumping over to the last layer, this has 10 neurons,
3:49
each representing one of the digits.
3:52
The activation in these neurons, again some number that's between 0 and 1,
3:56
represents how much the system thinks that a given image corresponds with a given digit.
4:03
There's also a couple layers in between called the hidden layers,
4:06
which for the time being should just be a giant question mark for
4:09
how on earth this process of recognizing digits is going to be handled.
4:14
In this network I chose two hidden layers, each one with 16 neurons,
4:17
and admittedly that's kind of an arbitrary choice.
4:21
To be honest I chose two layers based on how I want to motivate the structure in
4:24
just a moment, and 16, well that was just a nice number to fit on the screen.
4:28
In practice there is a lot of room for experiment with a specific structure here.
4:33
The way the network operates, activations in one
4:35
layer determine the activations of the next layer.
4:39
And of course the heart of the network as an information processing mechanism comes down
4:43
to exactly how those activations from one layer bring about activations in the next
4:48
layer.
4:49
It's meant to be loosely analogous to how in biological networks of neurons,
4:53
some groups of neurons firing cause certain others to fire.
4:58
Now the network I'm showing here has already been trained to recognize digits,
5:01
and let me show you what I mean by that.
5:03
It means if you feed in an image, lighting up all 784 neurons of the input layer
5:08
according to the brightness of each pixel in the image,
5:11
that pattern of activations causes some very specific pattern in the next layer
5:16
which causes some pattern in the one after it,
5:18
which finally gives some pattern in the output layer.
5:22
And the brightest neuron of that output layer is the network's choice,
5:26
so to speak, for what digit this image represents.
Why layers?
5:32
And before jumping into the math for how one layer influences the next,
5:36
or how training works, let's just talk about why it's even reasonable
5:40
to expect a layered structure like this to behave intelligently.
5:44
What are we expecting here?
5:45
What is the best hope for what those middle layers might be doing?
5:48
Well, when you or I recognize digits, we piece together various components.
5:54
A 9 has a loop up top and a line on the right.
5:57
An 8 also has a loop up top, but it's paired with another loop down low.
6:01
A 4 basically breaks down into three specific lines, and things like that.
6:07
Now in a perfect world, we might hope that each neuron in the second
6:11
to last layer corresponds with one of these subcomponents,
6:14
that anytime you feed in an image with, say, a loop up top,
6:18
like a 9 or an 8, there's some specific neuron whose activation is
6:22
going to be close to 1.
6:24
And I don't mean this specific loop of pixels,
6:26
the hope would be that any generally loopy pattern towards the top sets off this neuron.
6:32
That way, going from the third layer to the last one just requires
6:36
learning which combination of subcomponents corresponds to which digits.
6:41
Of course, that just kicks the problem down the road,
6:43
because how would you recognize these subcomponents,
6:45
or even learn what the right subcomponents should be?
6:48
And I still haven't even talked about how one layer influences the next,
6:51
but run with me on this one for a moment.
6:53
Recognizing a loop can also break down into subproblems.
6:57
One reasonable way to do this would be to first
6:59
recognize the various little edges that make it up.
7:03
Similarly, a long line, like the kind you might see in the digits 1 or 4 or 7,
7:08
is really just a long edge, or maybe you think of it as a certain pattern of several
7:13
smaller edges.
7:15
So maybe our hope is that each neuron in the second layer of
7:18
the network corresponds with the various relevant little edges.
7:23
Maybe when an image like this one comes in, it lights up all of the
7:27
neurons associated with around 8 to 10 specific little edges,
7:31
which in turn lights up the neurons associated with the upper loop
7:35
and a long vertical line, and those light up the neuron associated with a 9.
7:40
Whether or not this is what our final network actually does is another question,
7:44
one that I'll come back to once we see how to train the network,
7:47
but this is a hope that we might have, a sort of goal with the layered structure
7:51
like this.
7:53
Moreover, you can imagine how being able to detect edges and patterns
7:56
like this would be really useful for other image recognition tasks.
8:00
And even beyond image recognition, there are all sorts of intelligent
8:04
things you might want to do that break down into layers of abstraction.
8:08
Parsing speech, for example, involves taking raw audio and picking out distinct sounds,
8:12
which combine to make certain syllables, which combine to form words,
8:16
which combine to make up phrases and more abstract thoughts, etc.
8:21
But getting back to how any of this actually works,
8:23
picture yourself right now designing how exactly the activations in one layer might
8:27
determine the activations in the next.
8:30
The goal is to have some mechanism that could conceivably combine pixels into edges,
8:35
or edges into patterns, or patterns into digits.
Edge detection example
8:39
And to zoom in on one very specific example, let's say the hope
8:43
is for one particular neuron in the second layer to pick up
8:46
on whether or not the image has an edge in this region here.
8:51
The question at hand is what parameters should the network have?
8:55
What dials and knobs should you be able to tweak so that it's expressive
8:59
enough to potentially capture this pattern, or any other pixel pattern,
9:03
or the pattern that several edges can make a loop, and other such things?
9:08
Well, what we'll do is assign a weight to each one of the
9:11
connections between our neuron and the neurons from the first layer.
9:16
These weights are just numbers.
9:18
Then take all of those activations from the first layer
9:21
and compute their weighted sum according to these weights.
9:27
I find it helpful to think of these weights as being organized into a
9:31
little grid of their own, and I'm going to use green pixels to indicate
9:34
positive weights, and red pixels to indicate negative weights,
9:37
where the brightness of that pixel is some loose depiction of the weight's value.
9:42
Now if we made the weights associated with almost all of the pixels zero
9:46
except for some positive weights in this region that we care about,
9:50
then taking the weighted sum of all the pixel values really just amounts
9:53
to adding up the values of the pixel just in the region that we care about.
9:59
And if you really wanted to pick up on whether there's an edge here,
10:02
what you might do is have some negative weights associated with the surrounding pixels.
10:07
Then the sum is largest when those middle pixels
10:10
are bright but the surrounding pixels are darker.
10:14
When you compute a weighted sum like this, you might come out with any number,
10:18
but for this network what we want is for activations to be some value between 0 and 1.
10:24
So a common thing to do is to pump this weighted sum into some function
10:28
that squishes the real number line into the range between 0 and 1.
10:32
And a common function that does this is called the sigmoid function,
10:35
also known as a logistic curve.
10:38
Basically very negative inputs end up close to 0, positive inputs end up close to 1,
10:43
and it just steadily increases around the input 0.
10:49
So the activation of the neuron here is basically a
10:52
measure of how positive the relevant weighted sum is.
10:57
But maybe it's not that you want the neuron to
10:59
light up when the weighted sum is bigger than 0.
11:02
Maybe you only want it to be active when the sum is bigger than say 10.
11:06
That is, you want some bias for it to be inactive.
11:11
What we'll do then is just add in some other number like negative 10 to this
11:15
weighted sum before plugging it through the sigmoid squishification function.
11:20
That additional number is called the bias.
11:23
So the weights tell you what pixel pattern this neuron in the second
11:27
layer is picking up on, and the bias tells you how high the weighted
11:31
sum needs to be before the neuron starts getting meaningfully active.
Counting weights and biases
11:36
And that is just one neuron.
11:38
Every other neuron in this layer is going to be connected to
11:42
all 784 pixel neurons from the first layer, and each one of
11:46
those 784 connections has its own weight associated with it.
11:51
Also, each one has some bias, some other number that you add
11:54
on to the weighted sum before squishing it with the sigmoid.
11:58
And that's a lot to think about!
11:59
With this hidden layer of 16 neurons, that's a total of 784 times 16 weights,
12:06
along with 16 biases.
12:08
And all of that is just the connections from the first layer to the second.
12:12
The connections between the other layers also have
12:14
a bunch of weights and biases associated with them.
12:18
All said and done, this network has almost exactly 13,000 total weights and biases.
12:23
13,000 knobs and dials that can be tweaked and turned
12:27
to make this network behave in different ways.
How learning relates
12:31
So when we talk about learning, what that's referring to is
12:34
getting the computer to find a valid setting for all of these
12:37
many many numbers so that it'll actually solve the problem at hand.
12:42
One thought experiment that is at once fun and kind of horrifying is to imagine sitting
12:47
down and setting all of these weights and biases by hand,
12:50
purposefully tweaking the numbers so that the second layer picks up on edges,
12:54
the third layer picks up on patterns, etc.
12:56
I personally find this satisfying rather than just treating the network as a total black
13:01
box, because when the network doesn't perform the way you anticipate,
13:04
if you've built up a little bit of a relationship with what those weights and biases
13:09
actually mean, you have a starting place for experimenting with how to change the
13:13
structure to improve.
13:14
Or when the network does work but not for the reasons you might expect,
13:18
digging into what the weights and biases are doing is a good way to challenge
13:22
your assumptions and really expose the full space of possible solutions.
Notation and linear algebra
13:26
By the way, the actual function here is a little cumbersome to write down,
13:29
don't you think?
13:32
So let me show you a more notationally compact way that these connections are represented.
13:37
This is how you'd see it if you choose to read up more about neural networks.
13:40
Organize all of the activations from one layer into a column as a vector.
13:48
Then organize all of the weights as a matrix, where each row of that matrix corresponds
13:50
to the connections between one layer and a particular neuron in the next layer.
13:58
What that means is that taking the weighted sum of the activations in
14:02
the first layer according to these weights corresponds to one of the
14:05
terms in the matrix vector product of everything we have on the left here.
14:14
By the way, so much of machine learning just comes down to having a good
14:17
grasp of linear algebra, so for any of you who want a nice visual
14:21
understanding for matrices and what matrix vector multiplication means,
14:24
take a look at the series I did on linear algebra, especially chapter 3.
14:29
Back to our expression, instead of talking about adding the bias to each one of
14:33
these values independently, we represent it by organizing all those biases into
14:38
a vector, and adding the entire vector to the previous matrix vector product.
14:43
Then as a final step, I'll wrap a sigmoid around the outside here,
14:46
and what that's supposed to represent is that you're going to apply the
14:50
sigmoid function to each specific component of the resulting vector inside.
14:55
So once you write down this weight matrix and these vectors as their own symbols,
15:00
you can communicate the full transition of activations from one layer to the next in an
15:05
extremely tight and neat little expression, and this makes the relevant code both a lot
15:10
simpler and a lot faster, since many libraries optimize the heck out of matrix
15:14
multiplication.
Recap
15:17
Remember how earlier I said these neurons are simply things that hold numbers?
15:22
Well of course the specific numbers that they hold depends on the image you feed in,
15:27
so it's actually more accurate to think of each neuron as a function,
15:31
one that takes in the outputs of all the neurons in the previous layer and spits out a
15:36
number between 0 and 1.
15:39
Really the entire network is just a function, one that takes in
15:43
784 numbers as an input and spits out 10 numbers as an output.
15:47
It's an absurdly complicated function, one that involves 13,000 parameters
15:51
in the forms of these weights and biases that pick up on certain patterns,
15:55
and which involves iterating many matrix vector products and the sigmoid
15:59
squishification function, but it's just a function nonetheless.
16:03
And in a way it's kind of reassuring that it looks complicated.
16:07
I mean if it were any simpler, what hope would we have
16:09
that it could take on the challenge of recognizing digits?
16:13
And how does it take on that challenge?
16:15
How does this network learn the appropriate weights and biases just by looking at data?
16:20
Well that's what I'll show in the next video, and I'll also dig a little
16:23
more into what this particular network we're seeing is really doing.
Some final words
16:27
Now is the point I suppose I should say subscribe to stay notified
16:30
about when that video or any new videos come out,
16:33
but realistically most of you don't actually receive notifications from YouTube, do you?
16:38
Maybe more honestly I should say subscribe so that the neural networks
16:41
that underlie YouTube's recommendation algorithm are primed to believe
16:44
that you want to see content from this channel get recommended to you.
16:48
Anyway, stay posted for more.
16:50
Thank you very much to everyone supporting these videos on Patreon.
16:54
I've been a little slow to progress in the probability series this summer,
16:57
but I'm jumping back into it after this project,
16:59
so patrons you can look out for updates there.
ReLU vs Sigmoid
17:03
To close things off here I have with me Lisha Li who did her PhD work on the
17:07
theoretical side of deep learning and who currently works at a venture capital
17:10
firm called Amplify Partners who kindly provided some of the funding for this video.
17:15
So Lisha one thing I think we should quickly bring up is this sigmoid function.
17:19
As I understand it early networks use this to squish the relevant weighted
17:23
sum into that interval between zero and one, you know kind of motivated
17:26
by this biological analogy of neurons either being inactive or active.
17:30
Exactly. But relatively few modern networks actually use sigmoid anymore.
17:34
Yeah. It's kind of old school right?
17:35
Yeah or rather ReLU seems to be much easier to train.
17:39
And ReLU, ReLU stands for rectified linear unit?
17:42
Yes it's this kind of function where you're just taking a max of zero
17:47
and a where a is given by what you were explaining in the video and
17:52
what this was sort of motivated from I think was a partially by a
17:56
biological analogy with how neurons would either be activated or not.
18:01
And so if it passes a certain threshold it would be the identity function but if it did
18:06
not then it would just not be activated so it'd be zero so it's kind of a simplification.
18:11
Using sigmoids didn't help training or it was very difficult to
18:15
train at some point and people just tried ReLU and it happened
18:20
to work very well for these incredibly deep neural networks.
18:25
All right thank you Lisha.

------------

Gradient descent, how neural networks learn | Deep Learning Chapter 2

Video timeline
0:00 - Introduction
0:30 - Recap
1:49 - Using training data
3:01 - Cost functions
6:55 - Gradient descent
11:18 - More on gradient vectors
12:19 - Gradient descent recap
13:01 - Analyzing the network
16:37 - Learning more
17:38 - Lisha Li interview
19:58 - Closing thoughts



Introduction
0:04
Last video I laid out the structure of a neural network.
0:07
I'll give a quick recap here so that it's fresh in our minds,
0:10
and then I have two main goals for this video.
0:13
The first is to introduce the idea of gradient descent,
0:15
which underlies not only how neural networks learn,
0:18
but how a lot of other machine learning works as well.
0:21
Then after that we'll dig in a little more into how this particular network performs,
0:25
and what those hidden layers of neurons end up looking for.
0:28
As a reminder, our goal here is the classic example of handwritten digit recognition,
Recap
0:34
the hello world of neural networks.
0:37
These digits are rendered on a 28x28 pixel grid,
0:40
each pixel with some grayscale value between 0 and 1.
0:43
Those are what determine the activations of 784 neurons in the input layer of the network.
0:51
And then the activation for each neuron in the following layers is based on a weighted
0:55
sum of all the activations in the previous layer, plus some special number called a bias.
1:02
Then you compose that sum with some other function,
1:04
like the sigmoid squishification, or a relu, the way I walked through last video.
1:09
In total, given the somewhat arbitrary choice of two hidden layers with 16 neurons each,
1:15
the network has about 13,000 weights and biases that we can adjust,
1:19
and it's these values that determine what exactly the network actually does.
1:24
Then what we mean when we say that this network classifies a given digit is that
1:29
the brightest of those 10 neurons in the final layer corresponds to that digit.
1:34
And remember, the motivation we had in mind here for the layered structure
1:37
was that maybe the second layer could pick up on the edges,
1:41
and the third layer might pick up on patterns like loops and lines,
1:44
and the last one could just piece together those patterns to recognize digits.
Using training data
1:49
So here, we learn how the network learns.
1:52
What we want is an algorithm where you can show this network a whole bunch of
1:56
training data, which comes in the form of a bunch of different images of handwritten
2:01
digits, along with labels for what they're supposed to be,
2:04
and it'll adjust those 13,000 weights and biases so as to improve its performance
2:08
on the training data.
2:10
Hopefully, this layered structure will mean that what it
2:13
learns generalizes to images beyond that training data.
2:17
The way we test that is that after you train the network,
2:20
you show it more labeled data that it's never seen before,
2:23
and you see how accurately it classifies those new images.
2:31
Fortunately for us, and what makes this such a common example to start with,
2:34
is that the good people behind the MNIST database have put together a collection of tens
2:39
of thousands of handwritten digit images, each one labeled with the numbers they're
2:43
supposed to be.
2:44
And as provocative as it is to describe a machine as learning,
2:48
once you see how it works, it feels a lot less like some crazy sci-fi premise,
2:53
and a lot more like a calculus exercise.
2:56
I mean, basically it comes down to finding the minimum of a certain function.
Cost functions
3:01
Remember, conceptually, we're thinking of each neuron as being connected to all
3:06
the neurons in the previous layer, and the weights in the weighted sum defining
3:10
its activation are kind of like the strengths of those connections,
3:14
and the bias is some indication of whether that neuron tends to be active or inactive.
3:19
And to start things off, we're just going to initialize
3:22
all of those weights and biases totally randomly.
3:24
Needless to say, this network is going to perform pretty horribly on
3:27
a given training example, since it's just doing something random.
3:31
For example, you feed in this image of a 3, and the output layer just looks like a mess.
3:36
So what you do is define a cost function, a way of telling the computer,
3:41
no, bad computer, that output should have activations which are 0 for most neurons,
3:47
but 1 for this neuron, what you gave me is utter trash.
3:51
To say that a little more mathematically, you add up the squares of the differences
3:56
between each of those trash output activations and the value you want them to have,
4:01
and this is what we'll call the cost of a single training example.
4:05
Notice this sum is small when the network confidently classifies the image correctly,
4:11
but it's large when the network seems like it doesn't know what it's doing.
4:18
So then what you do is consider the average cost over all of
4:22
the tens of thousands of training examples at your disposal.
4:27
This average cost is our measure for how lousy the network is,
4:30
and how bad the computer should feel.
4:33
And that's a complicated thing.
4:35
Remember how the network itself was basically a function,
4:38
one that takes in 784 numbers as inputs, the pixel values,
4:42
and spits out 10 numbers as its output, and in a sense it's parameterized
4:46
by all these weights and biases?
4:49
Well the cost function is a layer of complexity on top of that.
4:53
It takes as its input those 13,000 or so weights and biases,
4:56
and spits out a single number describing how bad those weights and biases are,
5:01
and the way it's defined depends on the network's behavior over all the tens of
5:06
thousands of pieces of training data.
5:09
That's a lot to think about.
5:12
But just telling the computer what a crappy job it's doing isn't very helpful.
5:16
You want to tell it how to change those weights and biases so that it gets better.
5:20
To make it easier, rather than struggling to imagine a function with 13,000 inputs,
5:25
just imagine a simple function that has one number as an input and one number as an
5:30
output.
5:31
How do you find an input that minimizes the value of this function?
5:36
Calculus students will know that you can sometimes figure out that minimum explicitly,
5:41
but that's not always feasible for really complicated functions,
5:44
certainly not in the 13,000 input version of this situation for our crazy complicated
5:49
neural network cost function.
5:51
A more flexible tactic is to start at any input,
5:54
and figure out which direction you should step to make that output lower.
6:00
Specifically, if you can figure out the slope of the function where you are,
6:04
then shift to the left if that slope is positive,
6:06
and shift the input to the right if that slope is negative.
6:11
If you do this repeatedly, at each point checking the new slope and taking the
6:15
appropriate step, you're going to approach some local minimum of the function.
6:20
The image you might have in mind here is a ball rolling down a hill.
6:24
Notice, even for this really simplified single input function,
6:27
there are many possible valleys that you might land in,
6:30
depending on which random input you start at,
6:33
and there's no guarantee that the local minimum you land in is going to
6:36
be the smallest possible value of the cost function.
6:40
That will carry over to our neural network case as well.
6:43
And I also want you to notice how if you make your step sizes proportional to the slope,
6:47
then when the slope is flattening out towards the minimum,
6:50
your steps get smaller and smaller, and that kind of helps you from overshooting.
Gradient descent
6:55
Bumping up the complexity a bit, imagine instead
6:58
a function with two inputs and one output.
7:01
You might think of the input space as the xy-plane,
7:04
and the cost function as being graphed as a surface above it.
7:08
Now instead of asking about the slope of the function,
7:11
you have to ask which direction you should step in this input
7:15
space so as to decrease the output of the function most quickly.
7:19
In other words, what's the downhill direction?
7:22
Again, it's helpful to think of a ball rolling down that hill.
7:26
Those of you familiar with multivariable calculus will know that the
7:30
gradient of a function gives you the direction of steepest ascent,
7:34
which direction should you step to increase the function most quickly.
7:39
Naturally enough, taking the negative of that gradient gives you
7:42
the direction to step that decreases the function most quickly.
7:47
Even more than that, the length of this gradient vector is
7:50
an indication for just how steep that steepest slope is.
7:54
If you're unfamiliar with multivariable calculus and want to learn more,
7:57
check out some of the work I did for Khan Academy on the topic.
8:00
Honestly though, all that matters for you and me right now is that
8:04
in principle there exists a way to compute this vector,
8:07
this vector that tells you what the downhill direction is and how steep it is.
8:12
You'll be okay if that's all you know and you're not rock solid on the details.
8:17
Cause If you can get that, the algorithm for minimizing the function is to compute this
8:22
gradient direction, then take a small step downhill, and repeat that over and over.
8:27
It's the same basic idea for a function that has 13,000 inputs instead of 2 inputs.
8:33
Imagine organizing all 13,000 weights and biases
8:36
of our network into a giant column vector.
8:40
The negative gradient of the cost function is just a vector,
8:43
it's some direction inside this insanely huge input space that tells you which
8:48
nudges to all of those numbers is going to cause the most rapid decrease to
8:53
the cost function.
8:55
And of course, with our specially designed cost function,
8:58
changing the weights and biases to decrease it means making the
9:02
output of the network on each piece of training data look less like
9:06
a random array of 10 values, and more like an actual decision we want it to make.
9:11
It's important to remember, this cost function involves an average over all of the
9:15
training data, so if you minimize it, it means it's a better performance on all of those
9:20
samples.
9:23
The algorithm for computing this gradient efficiently,
9:26
which is effectively the heart of how a neural network learns,
9:29
is called backpropagation, and it's what I'm going to be talking about next video.
9:34
There, I really want to take the time to walk through what exactly happens to
9:38
each weight and bias for a given piece of training data,
9:41
trying to give an intuitive feel for what's happening beyond the pile of relevant
9:45
calculus and formulas.
9:47
Right here, right now, the main thing I want you to know,
9:50
independent of implementation details, is that what we mean when we
9:54
talk about a network learning is that it's just minimizing a cost function.
9:59
And notice, one consequence of that is that it's important for this cost function to have
10:03
a nice smooth output, so that we can find a local minimum by taking little steps
10:07
downhill.
10:09
This is why, by the way, artificial neurons have continuously ranging activations,
10:13
rather than simply being active or inactive in a binary way,
10:17
the way biological neurons are.
10:20
This process of repeatedly nudging an input of a function by some
10:23
multiple of the negative gradient is called gradient descent.
10:27
It's a way to converge towards some local minimum of a cost function,
10:30
basically a valley in this graph.
10:33
I'm still showing the picture of a function with two inputs, of course,
10:36
because nudges in a 13,000 dimensional input space are a little hard to
10:40
wrap your mind around, but there is a nice non-spatial way to think about this.
10:45
Each component of the negative gradient tells us two things.
10:49
The sign, of course, tells us whether the corresponding
10:51
component of the input vector should be nudged up or down.
10:55
But importantly, the relative magnitudes of all these
10:59
components kind of tells you which changes matter more.
11:05
You see, in our network, an adjustment to one of the weights might have a much
11:09
greater impact on the cost function than the adjustment to some other weight.
11:14
Some of these connections just matter more for our training data.
More on gradient vectors
11:19
So a way you can think about this gradient vector of our mind-warpingly massive
11:23
cost function is that it encodes the relative importance of each weight and bias,
11:28
that is, which of these changes is going to carry the most bang for your buck.
11:33
This really is just another way of thinking about direction.
11:37
To take a simpler example, if you have some function with two variables as an input,
11:41
and you compute that its gradient at some particular point comes out as 3,1,
11:46
then on the one hand you can interpret that as saying that when you're
11:50
standing at that input, moving along this direction increases the function most quickly,
11:55
that when you graph the function above the plane of input points,
11:58
that vector is what's giving you the straight uphill direction.
12:02
But another way to read that is to say that changes to this first variable have 3
12:07
times the importance as changes to the second variable,
12:10
that at least in the neighborhood of the relevant input,
12:13
nudging the x-value carries a lot more bang for your buck.
Gradient descent recap
12:19
Let's zoom out and sum up where we are so far.
12:22
The network itself is this function with 784 inputs and 10 outputs,
12:27
defined in terms of all these weighted sums.
12:30
The cost function is a layer of complexity on top of that.
12:33
It takes the 13,000 weights and biases as inputs and spits out
12:37
a single measure of lousiness based on the training examples.
12:42
And the gradient of the cost function is one more layer of complexity still.
12:47
It tells us what nudges to all these weights and biases cause the
12:50
fastest change to the value of the cost function,
12:53
which you might interpret as saying which changes to which weights matter the most.
Analyzing the network
13:02
So, when you initialize the network with random weights and biases,
13:06
and adjust them many times based on this gradient descent process,
13:09
how well does it actually perform on images it's never seen before?
13:14
The one I've described here, with the two hidden layers of 16 neurons each,
13:18
chosen mostly for aesthetic reasons, is not bad,
13:22
classifying about 96% of the new images it sees correctly.
13:26
And honestly, if you look at some of the examples it messes up on,
13:30
you feel compelled to cut it a little slack.
13:36
Now if you play around with the hidden layer structure and make a couple tweaks,
13:40
you can get this up to 98%.
13:41
And that's pretty good!
13:43
It's not the best, you can certainly get better performance by getting more sophisticated
13:47
than this plain vanilla network, but given how daunting the initial task is,
13:52
I think there's something incredible about any network doing this well on images it's
13:56
never seen before, given that we never specifically told it what patterns to look for.
14:02
Originally, the way I motivated this structure was by describing a hope we might have,
14:06
that the second layer might pick up on little edges,
14:09
that the third layer would piece together those edges to recognize loops
14:13
and longer lines, and that those might be pieced together to recognize digits.
14:17
So is this what our network is actually doing?
14:21
Well, for this one at least, not at all.
14:24
Remember how last video we looked at how the weights of the connections from all
14:28
the neurons in the first layer to a given neuron in the second layer can be
14:32
visualized as a given pixel pattern that the second layer neuron is picking up on?
14:37
Well, when we actually do that for the weights associated with these transitions,
14:42
from the first layer to the next, instead of picking up on isolated little edges here
14:47
and there, they look, well, almost random, just with some very loose patterns in the
14:52
middle there.
14:53
It would seem that in the unfathomably large 13,000 dimensional space
14:57
of possible weights and biases, our network found itself a happy
15:01
little local minimum that, despite successfully classifying most images,
15:05
doesn't exactly pick up on the patterns we might have hoped for.
15:09
And to really drive this point home, watch what happens when you input a random image.
15:14
If the system was smart, you might expect it to feel uncertain,
15:18
maybe not really activating any of those 10 output neurons or activating them
15:23
all evenly, but instead it confidently gives you some nonsense answer,
15:27
as if it feels as sure that this random noise is a 5 as it does that an actual
15:32
image of a 5 is a 5.
15:34
Phrased differently, even if this network can recognize digits pretty well,
15:38
it has no idea how to draw them.
15:41
A lot of this is because it's such a tightly constrained training setup.
15:45
I mean, put yourself in the network's shoes here.
15:48
From its point of view, the entire universe consists of nothing but clearly
15:52
defined unmoving digits centered in a tiny grid,
15:55
and its cost function never gave it any incentive to be anything but utterly
15:59
confident in its decisions.
16:02
So with this as the image of what those second layer neurons are really doing,
16:05
you might wonder why I would introduce this network with the
16:07
motivation of picking up on edges and patterns.
16:09
I mean, that's just not at all what it ends up doing.
16:13
Well, this is not meant to be our end goal, but instead a starting point.
16:17
Frankly, this is old technology, the kind researched in the 80s and 90s,
16:21
and you do need to understand it before you can understand more detailed modern
16:25
variants, and it clearly is capable of solving some interesting problems,
16:29
but the more you dig into what those hidden layers are really doing,
16:33
the less intelligent it seems.
Learning more
16:38
Shifting the focus for a moment from how networks learn to how you learn,
16:42
that'll only happen if you engage actively with the material here somehow.
16:47
One pretty simple thing I want you to do is just pause right now and think deeply
16:51
for a moment about what changes you might make to this system and how it perceives
16:56
images if you wanted it to better pick up on things like edges and patterns.
17:01
But better than that, to actually engage with the material,
17:04
I highly recommend the book by Michael Nielsen on deep learning and neural networks.
17:09
In it, you can find the code and the data to download and play with for this exact
17:14
example, and the book will walk you through step by step what that code is doing.
17:19
What's awesome is that this book is free and publicly available,
17:22
so if you do get something out of it, consider joining me in making a donation towards
17:26
Nielsen's efforts.
17:27
I've also linked a couple other resources I like a lot in the description,
17:31
including the phenomenal and beautiful blog post by Chris Ola and the articles in
17:36
Distill.
Lisha Li interview
17:38
To close things off here for the last few minutes,
17:40
I want to jump back into a snippet of the interview I had with Leisha Lee.
17:44
You might remember her from the last video, she did her PhD work in deep learning.
17:48
In this little snippet she talks about two recent papers that really dig into
17:52
how some of the more modern image recognition networks are actually learning.
17:56
Just to set up where we were in the conversation,
17:58
the first paper took one of these particularly deep neural networks that's really good
18:02
at image recognition, and instead of training it on a properly labeled dataset,
18:06
shuffled all the labels around before training.
18:09
Obviously the testing accuracy here was going to be no better than random,
18:13
since everything's just randomly labeled. But it was still able to achieve
18:17
the same training accuracy as you would on a properly labeled dataset.
18:21
Basically, the millions of weights for this particular network were
18:25
enough for it to just memorize the random data,
18:27
which raises the question for whether minimizing this cost function
18:31
actually corresponds to any sort of structure in the image, or is it just memorization?
18:51
...to memorize the entire dataset of what the correct classification is.
18:54
And so half a year later at ICML this year, there was not exactly rebuttal paper,
18:57
but paper that addressed some aspects of like, hey,
18:59
actually these networks are doing something a little bit smarter than that.
19:03
If you look at that accuracy curve if you were just training on a random data set
19:06
that curve went down very slowly, almost in a linear fashion.
19:08
So you’re really struggling to find that local minimum of the right weights.
19:12
Whereas if you're actually training on a structured dataset,
19:15
one that has the right labels, you fiddle around a little bit in the beginning,
19:20
but then you kind of dropped very fast to get to that accuracy level,
19:24
and so in some sense it was easier to find that local maxima.
19:28
And so what was also interesting about that is it brings into light another paper from
19:33
actually a couple of years ago, which has a lot more simplifications about the network
19:38
layers, but one of the results was saying how if you look at the optimization landscape,
19:43
the local minima that these networks tend to learn are actually of equal quality,
19:48
so in some sense if your dataset is structured,
19:51
you should be able to find that much more easily.
Closing thoughts
19:58
My thanks, as always, to those of you supporting on Patreon.
20:01
I've said before just what a game changer Patreon is,
20:04
but these videos really would not be possible without you.
20:07
I also want to give a special thanks to the VC firm Amplify Partners
20:10
and their support of these initial videos in the series. Thank you.

--

Backpropagation, intuitively | Deep Learning Chapter 3

Video timeline:
0:00 - Introduction
0:23 - Recap
3:07 - Intuitive walkthrough example
9:33 - Stochastic gradient descent
12:28 - Final words


Introduction
0:04
Here, we tackle backpropagation, the core algorithm behind how neural networks learn.
0:09
After a quick recap for where we are, the first thing I'll do is an intuitive walkthrough
0:13
for what the algorithm is actually doing, without any reference to the formulas.
0:17
Then, for those of you who do want to dive into the math,
0:20
the next video goes into the calculus underlying all this.
Recap
0:23
If you watched the last two videos, or if you're just jumping in with the appropriate
0:27
background, you know what a neural network is, and how it feeds forward information.
0:31
Here, we're doing the classic example of recognizing handwritten digits whose pixel
0:36
values get fed into the first layer of the network with 784 neurons,
0:39
and I've been showing a network with two hidden layers having just 16 neurons each,
0:43
and an output layer of 10 neurons, indicating which digit the network is choosing
0:48
as its answer.
0:50
I'm also expecting you to understand gradient descent,
0:53
as described in the last video, and how what we mean by learning is
0:56
that we want to find which weights and biases minimize a certain cost function.
1:02
As a quick reminder, for the cost of a single training example,
1:05
you take the output the network gives, along with the output you wanted it to give,
1:10
and add up the squares of the differences between each component.
1:15
Doing this for all of your tens of thousands of training examples and
1:18
averaging the results, this gives you the total cost of the network.
1:22
And as if that's not enough to think about, as described in the last video,
1:26
the thing that we're looking for is the negative gradient of this cost function,
1:30
which tells you how you need to change all of the weights and biases,
1:34
all of these connections, so as to most efficiently decrease the cost.
1:43
Backpropagation, the topic of this video, is an
1:45
algorithm for computing that crazy complicated gradient.
1:49
And the one idea from the last video that I really want you to hold firmly
1:52
in your mind right now is that because thinking of the gradient vector
1:56
as a direction in 13,000 dimensions is, to put it lightly,
1:59
beyond the scope of our imaginations, there's another way you can think about it.
2:04
The magnitude of each component here is telling you how
2:07
sensitive the cost function is to each weight and bias.
2:11
For example, let's say you go through the process I'm about to describe,
2:15
and you compute the negative gradient, and the component associated with the weight on
2:20
this edge here comes out to be 3.2, while the component associated with this edge here
2:25
comes out as 0.1.
2:26
The way you would interpret that is that the cost of the function is 32 times more
2:30
sensitive to changes in that first weight, so if you were to wiggle that value
2:34
just a little bit, it's going to cause some change to the cost,
2:38
and that change is 32 times greater than what the same wiggle to that second
2:42
weight would give.
2:48
Personally, when I was first learning about backpropagation,
2:51
I think the most confusing aspect was just the notation and the index chasing of it all.
2:56
But once you unwrap what each part of this algorithm is really doing,
2:59
each individual effect it's having is actually pretty intuitive,
3:02
it's just that there's a lot of little adjustments getting layered on top of each other.
Intuitive walkthrough example
3:07
So I'm going to start things off here with a complete disregard for the notation,
3:11
and just step through the effects each training example has on the weights and biases.
3:17
Because the cost function involves averaging a certain cost per example over all
3:21
the tens of thousands of training examples, the way we adjust the weights and
3:26
biases for a single gradient descent step also depends on every single example.
3:31
Or rather, in principle it should, but for computational efficiency we'll do a little
3:35
trick later to keep you from needing to hit every single example for every step.
3:39
In other cases, right now, all we're going to do is focus
3:42
our attention on one single example, this image of a 2.
3:46
What effect should this one training example have
3:49
on how the weights and biases get adjusted?
3:52
Let's say we're at a point where the network is not well trained yet,
3:56
so the activations in the output are going to look pretty random,
3:59
maybe something like 0.5, 0.8, 0.2, on and on.
4:02
We can't directly change those activations, we
4:04
only have influence on the weights and biases.
4:07
But it's helpful to keep track of which adjustments
4:09
we wish should take place to that output layer.
4:13
And since we want it to classify the image as a 2,
4:16
we want that third value to get nudged up while all the others get nudged down.
4:22
Moreover, the sizes of these nudges should be proportional
4:25
to how far away each current value is from its target value.
4:30
For example, the increase to that number 2 neuron's activation
4:33
is in a sense more important than the decrease to the number 8 neuron,
4:37
which is already pretty close to where it should be.
4:42
So zooming in further, let's focus just on this one neuron,
4:44
the one whose activation we wish to increase.
4:48
Remember, that activation is defined as a certain weighted sum of all the
4:52
activations in the previous layer, plus a bias,
4:55
which is all then plugged into something like the sigmoid squishification function,
5:00
or a ReLU.
5:01
So there are three different avenues that can team
5:04
up together to help increase that activation.
5:07
You can increase the bias, you can increase the weights,
5:10
and you can change the activations from the previous layer.
5:14
Focusing on how the weights should be adjusted,
5:17
notice how the weights actually have differing levels of influence.
5:21
The connections with the brightest neurons from the preceding layer have the
5:25
biggest effect since those weights are multiplied by larger activation values.
5:31
So if you were to increase one of those weights,
5:33
it actually has a stronger influence on the ultimate cost function than increasing
5:38
the weights of connections with dimmer neurons,
5:40
at least as far as this one training example is concerned.
5:44
Remember, when we talk about gradient descent,
5:46
we don't just care about whether each component should get nudged up or down,
5:50
we care about which ones give you the most bang for your buck.
5:55
This, by the way, is at least somewhat reminiscent of a theory in
5:58
neuroscience for how biological networks of neurons learn, Hebbian theory,
6:02
often summed up in the phrase, neurons that fire together wire together.
6:07
Here, the biggest increases to weights, the biggest strengthening of connections,
6:11
happens between neurons which are the most active,
6:14
and the ones which we wish to become more active.
6:17
In a sense, the neurons that are firing while seeing a 2 get
6:21
more strongly linked to those firing when thinking about a 2.
6:25
To be clear, I'm not in a position to make statements one way or another about
6:29
whether artificial networks of neurons behave anything like biological brains,
6:33
and this fires together wire together idea comes with a couple meaningful asterisks,
6:37
but taken as a very loose analogy, I find it interesting to note.
6:41
Anyway, the third way we can help increase this neuron's activation
6:45
is by changing all the activations in the previous layer.
6:49
Namely, if everything connected to that digit 2 neuron with a positive
6:53
weight got brighter, and if everything connected with a negative weight got dimmer,
6:57
then that digit 2 neuron would become more active.
7:02
And similar to the weight changes, you're going to get the most bang for your buck
7:06
by seeking changes that are proportional to the size of the corresponding weights.
7:12
Now of course, we cannot directly influence those activations,
7:15
we only have control over the weights and biases.
7:17
But just as with the last layer, it's helpful to
7:20
keep a note of what those desired changes are.
7:24
But keep in mind, zooming out one step here, this
7:26
is only what that digit 2 output neuron wants.
7:29
Remember, we also want all the other neurons in the last layer to become less active,
7:33
and each of those other output neurons has its own thoughts about
7:37
what should happen to that second to last layer.
7:42
So, the desire of this digit 2 neuron is added together with the desires
7:47
of all the other output neurons for what should happen to this second to last layer,
7:52
again in proportion to the corresponding weights,
7:56
and in proportion to how much each of those neurons needs to change.
8:01
This right here is where the idea of propagating backwards comes in.
8:05
By adding together all these desired effects, you basically get a
8:09
list of nudges that you want to happen to this second to last layer.
8:14
And once you have those, you can recursively apply the same process to the
8:17
relevant weights and biases that determine those values,
8:20
repeating the same process I just walked through and moving backwards
8:24
through the network.
8:28
And zooming out a bit further, remember that this is all just how a single
8:33
training example wishes to nudge each one of those weights and biases.
8:37
If we only listened to what that 2 wanted, the network would
8:40
ultimately be incentivized just to classify all images as a 2.
8:44
So what you do is go through this same backprop routine for every other training example,
8:49
recording how each of them would like to change the weights and biases,
8:53
and average together those desired changes.
9:01
This collection here of the averaged nudges to each weight and bias is,
9:05
loosely speaking, the negative gradient of the cost function referenced
9:10
in the last video, or at least something proportional to it.
9:14
I say loosely speaking only because I have yet to get quantitatively precise
9:18
about those nudges, but if you understood every change I just referenced,
9:22
why some are proportionally bigger than others,
9:24
and how they all need to be added together, you understand the mechanics for
9:28
what backpropagation is actually doing.
Stochastic gradient descent
9:33
By the way, in practice, it takes computers an extremely long time to add
9:38
up the influence of every training example every gradient descent step.
9:43
So here's what's commonly done instead.
9:45
You randomly shuffle your training data and then divide it into a whole
9:48
bunch of mini-batches, let's say each one having 100 training examples.
9:52
Then you compute a step according to the mini-batch.
9:56
It's not going to be the actual gradient of the cost function,
10:00
which depends on all of the training data, not this tiny subset,
10:03
so it's not the most efficient step downhill,
10:05
but each mini-batch does give you a pretty good approximation, and more importantly,
10:09
it gives you a significant computational speedup.
10:12
If you were to plot the trajectory of your network under the relevant cost surface,
10:17
it would be a little more like a drunk man stumbling aimlessly down a hill but taking
10:21
quick steps, rather than a carefully calculating man determining the exact downhill
10:25
direction of each step before taking a very slow and careful step in that direction.
10:31
This technique is referred to as stochastic gradient descent.
10:35
There's a lot going on here, so let's just sum it up for ourselves, shall we?
10:40
Backpropagation is the algorithm for determining how a single training
10:44
example would like to nudge the weights and biases,
10:47
not just in terms of whether they should go up or down,
10:50
but in terms of what relative proportions to those changes cause the
10:53
most rapid decrease to the cost.
10:56
A true gradient descent step would involve doing this for all your tens of
11:00
thousands of training examples and averaging the desired changes you get.
11:04
But that's computationally slow, so instead you randomly subdivide the
11:08
data into mini-batches and compute each step with respect to a mini-batch.
11:14
Repeatedly going through all of the mini-batches and making these adjustments,
11:17
you will converge towards a local minimum of the cost function,
11:21
which is to say your network will end up doing a really good job on the training
11:25
examples.
11:27
So with all of that said, every line of code that would go into implementing backprop
11:32
actually corresponds with something you have now seen, at least in informal terms.
11:37
But sometimes knowing what the math does is only half the battle,
11:40
and just representing the damn thing is where it gets all muddled and confusing.
11:44
So for those of you who do want to go deeper, the next video goes through the same
11:48
ideas that were just presented here, but in terms of the underlying calculus,
11:52
which should hopefully make it a little more familiar as you see the topic in other
11:55
resources.
11:57
Before that, one thing worth emphasizing is that for this algorithm to work,
12:00
and this goes for all sorts of machine learning beyond just neural networks,
12:04
you need a lot of training data.
12:06
In our case, one thing that makes handwritten digits such a nice example is that there
12:10
exists the MNIST database, with so many examples that have been labeled by humans.
12:15
So a common challenge that those of you working in machine learning will be familiar with
12:19
is just getting the labeled training data you actually need,
12:21
whether that's having people label tens of thousands of images,
12:24
or whatever other data type you might be dealing with.

----

Backpropagation calculus | Deep Learning Chapter 4

Video timeline
0:00 - Introduction
0:38 - The Chain Rule in networks
3:56 - Computing relevant derivatives
4:45 - What do the derivatives mean?
5:39 - Sensitivity to weights/biases
6:42 - Layers with additional neurons
9:13 - Recap



Introduction
0:00
[Submit subtitle corrections at criblate.com]
0:04
The hard assumption here is that you've watched part 3,
0:06
giving an intuitive walkthrough of the backpropagation algorithm.
0:11
Here we get a little more formal and dive into the relevant calculus.
0:14
It's normal for this to be at least a little confusing,
0:17
so the mantra to regularly pause and ponder certainly applies as much here
0:20
as anywhere else.
0:21
Our main goal is to show how people in machine learning commonly think about
0:25
the chain rule from calculus in the context of networks,
0:28
which has a different feel from how most introductory calculus courses
0:32
approach the subject.
0:34
For those of you uncomfortable with the relevant calculus,
0:36
I do have a whole series on the topic.
The Chain Rule in networks
0:39
Let's start off with an extremely simple network,
0:43
one where each layer has a single neuron in it.
0:46
This network is determined by three weights and three biases,
0:49
and our goal is to understand how sensitive the cost function is to these variables.
0:55
That way, we know which adjustments to those terms will
0:58
cause the most efficient decrease to the cost function.
1:01
And we're just going to focus on the connection between the last two neurons.
1:05
Let's label the activation of that last neuron with a superscript L,
1:10
indicating which layer it's in, so the activation of the previous neuron is a^(L-1).
1:16
These are not exponents, they're just a way of indexing what we're talking about,
1:20
since I want to save subscripts for different indices later on.
1:23
Let's say that the value we want this last activation to be for
1:27
a given training example is y, for example, y might be 0 or 1.
1:32
So the cost of this network for a single training example is a^(L - y) squared.
1:40
We'll denote the cost of that one training example as C0.
1:45
As a reminder, this last activation is determined by a weight,
1:49
which I'm going to call w(L), times the previous neuron's activation plus some bias,
1:55
which I'll call b(L).
1:57
And then you pump that through some special nonlinear function like the sigmoid or ReLU.
2:01
It's actually going to make things easier for us if we give a special name to
2:05
this weighted sum, like z, with the same superscript as the relevant activations.
2:10
This is a lot of terms, and a way you might conceptualize it is that the weight,
2:15
previous action and the bias all together are used to compute z,
2:19
which in turn lets us compute a, which finally, along with a constant y,
2:23
lets us compute the cost.
2:27
And of course a(L-1) is influenced by its own weight and bias and such...
2:31
but we're not going to focus on that right now.
2:35
All of these are just numbers, right?
2:38
And it can be nice to think of each one as having its own little number line.
2:41
Our first goal is to understand how sensitive the
2:45
cost function is to small changes in our weight w(L).
2:49
Or phrased differently, what is the derivative of C with respect to w(L)?
2:55
When you see this del w term, think of it as meaning some tiny nudge to W,
3:00
like a change by 0.01, and think of this del C term as meaning
3:04
whatever the resulting nudge to the cost is.
3:08
What we want is their ratio.
3:11
Conceptually, this tiny nudge to w(L) causes some nudge to z(L),
3:15
which in turn causes some nudge to a(L), which directly influences the cost.
3:23
So we break things up by first looking at the ratio of a tiny change to z(L) to
3:28
this tiny change w(L), that is, the derivative of z(L) with respect to w(L).
3:33
Likewise, you then consider the ratio of the change to a(L) to
3:36
the tiny change in z(L) that caused it, as well as the ratio
3:40
between the final nudge to C and this intermediate nudge to a(L).
3:45
This right here is the chain rule, where multiplying together these
3:50
three ratios gives us the sensitivity of C to small changes in w(L).
Computing relevant derivatives
3:56
So on screen right now, there's a lot of symbols,
3:59
and take a moment to make sure it's clear what they all are,
4:02
because now we're going to compute the relevant derivatives.
4:07
The derivative of C with respect to a(L) works out to be 2(a(L)-y).
4:13
Notice this means its size is proportional to the difference between the network's
4:18
output and the thing we want it to be, so if that output was very different,
4:22
even slight changes stand to have a big impact on the final cost function.
4:27
The derivative of a(L) with respect to z(L) is just the derivative
4:31
of our sigmoid function, or whatever nonlinearity you choose to use.
4:37
And the derivative of z(L) with respect to w(L)... In this case comes out to be a(L-1).
What do the derivatives mean?
4:45
Now I don't know about you, but I think it's easy to get stuck head down in the
4:49
formulas without taking a moment to sit back and remind yourself of what they all mean.
4:53
In the case of this last derivative, the amount that the small nudge to the
4:58
weight influenced the last layer depends on how strong the previous neuron is.
5:03
Remember, this is where the neurons-that-fire-together-wire-together idea comes in.
5:09
And all of this is the derivative with respect to w(L)
5:12
only of the cost for a specific single training example.
5:16
Since the full cost function involves averaging together all
5:19
those costs across many different training examples,
5:22
its derivative requires averaging this expression over all training examples.
5:28
And of course, that is just one component of the gradient vector,
5:31
which itself is built up from the partial derivatives of the
5:35
cost function with respect to all those weights and biases.
Sensitivity to weights/biases
5:40
But even though that's just one of the many partial derivatives we need,
5:43
it's more than 50% of the work.
5:46
The sensitivity to the bias, for example, is almost identical.
5:50
We just need to change out this del z del w term for a del z del b.
5:58
And if you look at the relevant formula, that derivative comes out to be 1.
6:06
Also, and this is where the idea of propagating backwards comes in,
6:10
you can see how sensitive this cost function is to the activation of the previous layer.
6:15
Namely, this initial derivative in the chain rule expression,
6:19
the sensitivity of z to the previous activation, comes out to be the weight w(L).
6:26
And again, even though we're not going to be able to directly influence
6:30
that previous layer activation, it's helpful to keep track of,
6:33
because now we can just keep iterating this same chain rule idea backwards
6:37
to see how sensitive the cost function is to previous weights and previous biases.
Layers with additional neurons
6:43
And you might think this is an overly simple example, since all layers have one neuron,
6:47
and things are going to get exponentially more complicated for a real network.
6:51
But honestly, not that much changes when we give the layers multiple neurons,
6:55
really it's just a few more indices to keep track of.
6:59
Rather than the activation of a given layer simply being a(L),
7:02
it's also going to have a subscript indicating which neuron of that layer it is.
7:07
Let's use the letter k to index the layer L-1, and j to index the layer L.
7:15
For the cost, again we look at what the desired output is,
7:18
but this time we add up the squares of the differences between these last layer
7:23
activations and the desired output.
7:26
That is, you take a sum over a(L)j minus yj squared.
7:33
Since there's a lot more weights, each one has to have a couple more
7:37
indices to keep track of where it is, so let's call the weight of
7:41
the edge connecting this kth neuron to the jth neuron, w(L)_jk.
7:45
Those indices might feel a little backwards at first,
7:48
but it lines up with how you'd index the weight matrix I talked about in
7:52
the part 1 video.
7:53
Just as before, it's still nice to give a name to the relevant weighted sum,
7:57
like z, so that the activation of the last layer is just your special function,
8:02
like the sigmoid, applied to z.
8:04
You can see what I mean, where all of these are essentially the same equations we had
8:08
before in the one-neuron-per-layer case, it's just that it looks a little more
8:13
complicated.
8:15
And indeed, the chain-ruled derivative expression describing how
8:19
sensitive the cost is to a specific weight looks essentially the same.
8:23
I'll leave it to you to pause and think about each of those terms if you want.
8:28
What does change here, though, is the derivative of the cost
8:32
with respect to one of the activations in the layer L-1.
8:37
In this case, the difference is that the neuron influences
8:40
the cost function through multiple different paths.
8:44
That is, on the one hand, it influences a(L)0, which plays a role in the cost function,
8:50
but it also has an influence on a(L)1, which also plays a role in the cost function,
8:55
and you have to add those up.
8:59
And that, well, that's pretty much it.
9:03
Once you know how sensitive the cost function is to the
9:06
activations in this second-to-last layer, you can just repeat
9:09
the process for all the weights and biases feeding into that layer.
Recap
9:13
So pat yourself on the back!
9:15
If all of this makes sense, you have now looked deep into the heart of backpropagation,
9:20
the workhorse behind how neural networks learn.
9:23
These chain rule expressions give you the derivatives that determine each component in
9:28
the gradient that helps minimize the cost of the network by repeatedly stepping downhill.
9:34
If you sit back and think about all that, this is a lot of layers of complexity to
9:38
wrap your mind around, so don't worry if it takes time for your mind to digest it all.

---
Large Language Models explained briefly


0:01
Imagine you happen across a short movie script that
0:03
describes a scene between a person and their AI assistant.
0:07
The script has what the person asks the AI, but the AI's response has been torn off.
0:13
Suppose you also have this powerful magical machine that can take
0:16
any text and provide a sensible prediction of what word comes next.
0:21
You could then finish the script by feeding in what you have to the machine,
0:25
seeing what it would predict to start the AI's answer,
0:28
and then repeating this over and over with a growing script completing the dialogue.
0:33
When you interact with a chatbot, this is exactly what's happening.
0:37
A large language model is a sophisticated mathematical function
0:40
that predicts what word comes next for any piece of text.
0:44
Instead of predicting one word with certainty, though,
0:47
what it does is assign a probability to all possible next words.
0:51
To build a chatbot, you lay out some text that describes an interaction between a user
0:56
and a hypothetical AI assistant, add on whatever the user types in as the first part of
1:02
the interaction, and then have the model repeatedly predict the next word that such a
1:07
hypothetical AI assistant would say in response, and that's what's presented to the user.
1:13
In doing this, the output tends to look a lot more natural if
1:16
you allow it to select less likely words along the way at random.
1:20
So what this means is even though the model itself is deterministic,
1:23
a given prompt typically gives a different answer each time it's run.
1:28
Models learn how to make these predictions by processing an enormous amount of text,
1:32
typically pulled from the internet.
1:34
For a standard human to read the amount of text that was used to train GPT-3,
1:39
for example, if they read non-stop 24-7, it would take over 2600 years.
1:44
Larger models since then train on much, much more.
1:48
You can think of training a little bit like tuning the dials on a big machine.
1:52
The way that a language model behaves is entirely determined by these
1:56
many different continuous values, usually called parameters or weights.
2:01
Changing those parameters will change the probabilities
2:04
that the model gives for the next word on a given input.
2:07
What puts the large in large language model is how
2:10
they can have hundreds of billions of these parameters.
2:15
No human ever deliberately sets those parameters.
2:18
Instead, they begin at random, meaning the model just outputs gibberish,
2:22
but they're repeatedly refined based on many example pieces of text.
2:27
One of these training examples could be just a handful of words,
2:30
or it could be thousands, but in either case, the way this works is to
2:34
pass in all but the last word from that example into the model and
2:38
compare the prediction that it makes with the true last word from the example.
2:43
An algorithm called backpropagation is used to tweak all of the parameters
2:47
in such a way that it makes the model a little more likely to choose
2:51
the true last word and a little less likely to choose all the others.
2:55
When you do this for many, many trillions of examples,
2:58
not only does the model start to give more accurate predictions on the training data,
3:03
but it also starts to make more reasonable predictions on text that it's never
3:07
seen before.
3:09
Given the huge number of parameters and the enormous amount of training data,
3:13
the scale of computation involved in training a large language model is mind-boggling.
3:19
To illustrate, imagine that you could perform one
3:22
billion additions and multiplications every single second.
3:26
How long do you think it would take for you to do all of the
3:29
operations involved in training the largest language models?
3:33
Do you think it would take a year?
3:36
Maybe something like 10,000 years?
3:39
The answer is actually much more than that.
3:41
It's well over 100 million years.
3:45
This is only part of the story, though.
3:47
This whole process is called pre-training.
3:49
The goal of auto-completing a random passage of text from the
3:52
internet is very different from the goal of being a good AI assistant.
3:56
To address this, chatbots undergo another type of training,
4:00
just as important, called reinforcement learning with human feedback.
4:04
Workers flag unhelpful or problematic predictions,
4:07
and their corrections further change the model's parameters,
4:11
making them more likely to give predictions that users prefer.
4:14
Looking back at the pre-training, though, this staggering amount of
4:18
computation is only made possible by using special computer chips that
4:23
are optimized for running many operations in parallel, known as GPUs.
4:28
However, not all language models can be easily parallelized.
4:32
Prior to 2017, most language models would process text one word at a time,
4:36
but then a team of researchers at Google introduced a new model known as the transformer.
4:43
Transformers don't read text from the start to the finish,
4:46
they soak it all in at once, in parallel.
4:49
The very first step inside a transformer, and most other language models for that matter,
4:54
is to associate each word with a long list of numbers.
4:57
The reason for this is that the training process only works with continuous values,
5:02
so you have to somehow encode language using numbers,
5:05
and each of these lists of numbers may somehow encode the meaning of the
5:09
corresponding word.
5:10
What makes transformers unique is their reliance
5:13
on a special operation known as attention.
5:16
This operation gives all of these lists of numbers a chance to talk to one another
5:21
and refine the meanings they encode based on the context around, all done in parallel.
5:27
For example, the numbers encoding the word bank might be changed based on the
5:31
context surrounding it to somehow encode the more specific notion of a riverbank.
5:37
Transformers typically also include a second type of operation known
5:41
as a feed-forward neural network, and this gives the model extra
5:44
capacity to store more patterns about language learned during training.
5:49
All of this data repeatedly flows through many different iterations of
5:53
these two fundamental operations, and as it does so,
5:56
the hope is that each list of numbers is enriched to encode whatever
6:00
information might be needed to make an accurate prediction of what word
6:04
follows in the passage.
6:07
At the end, one final function is performed on the last vector in this sequence,
6:11
which now has had a chance to be influenced by all the other context from the input text,
6:16
as well as everything the model learned during training,
6:19
to produce a prediction of the next word.
6:22
Again, the model's prediction looks like a probability for every possible next word.
6:28
Although researchers design the framework for how each of these steps work,
6:32
it's important to understand that the specific behavior is an emergent phenomenon
6:37
based on how those hundreds of billions of parameters are tuned during training.
6:42
This makes it incredibly challenging to determine
6:45
why the model makes the exact predictions that it does.
6:48
What you can see is that when you use large language model predictions to autocomplete
6:53
a prompt, the words that it generates are uncannily fluent, fascinating, and even useful.
7:05
If you're a new viewer and you're curious about more details on how
7:08
transformers and attention work, boy do I have some material for you.
7:12
One option is to jump into a series I made about deep learning,
7:16
where we visualize and motivate the details of attention and all the other steps
7:20
in a transformer.
7:22
Also, on my second channel I just posted a talk I gave a couple
7:25
months ago about this topic for the company TNG in Munich.
7:29
Sometimes I actually prefer the content I make as a casual talk rather than a produced
7:33
video, but I leave it up to you which one of these feels like the better follow-on.

----

Transformers, the tech behind LLMs | Deep Learning Chapter 5

Timestamps

0:00 - Predict, sample, repeat
3:03 - Inside a transformer
6:36 - Chapter layout
7:20 - The premise of Deep Learning
12:27 - Word embeddings
18:25 - Embeddings beyond words
20:22 - Unembedding
22:22 - Softmax with temperature
26:03 - Up next


Predict, sample, repeat
0:00
The initials GPT stand for Generative Pretrained Transformer.
0:05
So that first word is straightforward enough, these are bots that generate new text.
0:09
Pretrained refers to how the model went through a process of learning
0:13
from a massive amount of data, and the prefix insinuates that there's
0:16
more room to fine-tune it on specific tasks with additional training.
0:20
But the last word, that's the real key piece.
0:23
A transformer is a specific kind of neural network, a machine learning model,
0:27
and it's the core invention underlying the current boom in AI.
0:31
What I want to do with this video and the following chapters is go through a
0:35
visually-driven explanation for what actually happens inside a transformer.
0:39
We're going to follow the data that flows through it and go step by step.
0:43
There are many different kinds of models that you can build using transformers.
0:47
Some models take in audio and produce a transcript.
0:51
This sentence comes from a model going the other way around,
0:54
producing synthetic speech just from text.
0:56
All those tools that took the world by storm in 2022 like DALL-E and Midjourney
1:01
that take in a text description and produce an image are based on transformers.
1:06
Even if I can't quite get it to understand what a pi creature is supposed to be,
1:09
I'm still blown away that this kind of thing is even remotely possible.
1:13
And the original transformer introduced in 2017 by Google was invented for
1:18
the specific use case of translating text from one language into another.
1:22
But the variant that you and I will focus on, which is the type that
1:26
underlies tools like ChatGPT, will be a model that's trained to take in a piece of text,
1:31
maybe even with some surrounding images or sound accompanying it,
1:34
and produce a prediction for what comes next in the passage.
1:38
That prediction takes the form of a probability distribution
1:41
over many different chunks of text that might follow.
1:45
At first glance, you might think that predicting the next word
1:47
feels like a very different goal from generating new text.
1:50
But once you have a prediction model like this,
1:52
a simple thing you could try to make it generate, a longer piece of text,
1:56
is to give it an initial snippet to work with,
1:58
have it take a random sample from the distribution it just generated,
2:02
append that sample to the text, and then run the whole process again to make
2:05
a new prediction based on all the new text, including what it just added.
2:10
I don't know about you, but it really doesn't feel like this should actually work.
2:13
In this animation, for example, I'm running GPT-2 on my laptop and having it repeatedly
2:17
predict and sample the next chunk of text to generate a story based on the seed text.
2:22
The story just doesn't actually really make that much sense.
2:26
But if I swap it out for API calls to GPT-3 instead, which is the same basic model,
2:31
just much bigger, suddenly almost magically we do get a sensible story,
2:35
one that even seems to infer that a pi creature would live in a land of math and
2:40
computation.
2:41
This process here of repeated prediction and sampling is essentially
2:44
what's happening when you interact with ChatGPT,
2:47
or any of these other large language models, and you see them producing
2:50
one word at a time.
2:52
In fact, one feature that I would very much enjoy is the ability to
2:55
see the underlying distribution for each new word that it chooses.
Inside a transformer
3:03
Let's kick things off with a very high level preview
3:06
of how data flows through a transformer.
3:08
We will spend much more time motivating and interpreting and expanding
3:11
on the details of each step, but in broad strokes,
3:14
when one of these chatbots generates a given word, here's what's going on under the hood.
3:19
First, the input is broken up into a bunch of little pieces.
3:22
These pieces are called tokens, and in the case of text these tend to be
3:26
words or little pieces of words or other common character combinations.
3:30
If images or sound are involved, then tokens could be little
3:34
patches of that image or little chunks of that sound.
3:37
Each one of these tokens is then associated with a vector, meaning some list of numbers,
3:42
which is meant to somehow encode the meaning of that piece.
3:45
If you think of these vectors as giving coordinates in some very high dimensional space,
3:50
words with similar meanings tend to land on vectors that are
3:53
close to each other in that space.
3:55
This sequence of vectors then passes through an operation that's
3:58
known as an attention block, and this allows the vectors to talk to
4:01
each other and pass information back and forth to update their values.
4:04
For example, the meaning of the word model in the phrase "a machine learning
4:08
model" is different from its meaning in the phrase "a fashion model".
4:12
The attention block is what's responsible for figuring out which
4:15
words in context are relevant to updating the meanings of which other words,
4:19
and how exactly those meanings should be updated.
4:22
And again, whenever I use the word meaning, this is
4:25
somehow entirely encoded in the entries of those vectors.
4:29
After that, these vectors pass through a different kind of operation,
4:32
and depending on the source that you're reading this will be referred
4:35
to as a multi-layer perceptron or maybe a feed-forward layer.
4:38
And here the vectors don't talk to each other,
4:40
they all go through the same operation in parallel.
4:43
And while this block is a little bit harder to interpret,
4:45
later on we'll talk about how the step is a little bit like asking a long list
4:49
of questions about each vector, and then updating them based on the answers
4:53
to those questions.
4:54
All of the operations in both of these blocks look like a
4:58
giant pile of matrix multiplications, and our primary job is
5:01
going to be to understand how to read the underlying matrices.
5:06
I'm glossing over some details about some normalization steps that happen in between,
5:10
but this is after all a high-level preview.
5:13
After that, the process essentially repeats, you go back and forth
5:17
between attention blocks and multi-layer perceptron blocks,
5:20
until at the very end the hope is that all of the essential meaning
5:24
of the passage has somehow been baked into the very last vector in the sequence.
5:28
We then perform a certain operation on that last vector that produces a probability
5:33
distribution over all possible tokens, all possible little chunks of text that might
5:37
come next.
5:38
And like I said, once you have a tool that predicts what comes next
5:42
given a snippet of text, you can feed it a little bit of seed text and
5:45
have it repeatedly play this game of predicting what comes next,
5:49
sampling from the distribution, appending it, and then repeating over and over.
5:53
Some of you in the know may remember how long before ChatGPT came into the scene,
5:57
this is what early demos of GPT-3 looked like,
6:00
you would have it autocomplete stories and essays based on an initial snippet.
6:05
To make a tool like this into a chatbot, the easiest starting point is to have a
6:09
little bit of text that establishes the setting of a user interacting with a
6:13
helpful AI assistant, what you would call the system prompt,
6:17
and then you would use the user's initial question or prompt as the first bit of
6:21
dialogue, and then you have it start predicting what such a helpful AI assistant
6:25
would say in response.
6:27
There is more to say about an added step of training that's required
6:30
to make this work well, but at a high level this is the idea.
6:35
In this chapter, you and I are going to expand on the details of what happens at the very
Chapter layout
6:39
beginning of the network, at the very end of the network,
6:42
and I also want to spend a lot of time reviewing some important bits of background
6:46
knowledge, things that would have been second nature to any machine learning engineer by
6:50
the time transformers came around.
6:53
If you're comfortable with that background knowledge and a little impatient,
6:56
you could probably feel free to skip to the next chapter,
6:58
which is going to focus on the attention blocks,
7:00
generally considered the heart of the transformer.
7:03
After that, I want to talk more about these multi-layer perceptron blocks,
7:06
how training works, and a number of other details that will have been skipped up to
7:11
that point.
7:12
For broader context, these videos are additions to a mini-series about deep learning,
7:16
and it's okay if you haven't watched the previous ones,
7:18
I think you can do it out of order, but before diving into transformers specifically,
The premise of Deep Learning
7:22
I do think it's worth making sure that we're on the same page about the basic premise
7:27
and structure of deep learning.
7:29
At the risk of stating the obvious, this is one approach to machine learning,
7:33
which describes any model where you're using data to somehow determine how a model
7:37
behaves.
7:39
What I mean by that is, let's say you want a function that takes in
7:42
an image and it produces a label describing it,
7:44
or our example of predicting the next word given a passage of text,
7:48
or any other task that seems to require some element of intuition
7:51
and pattern recognition.
7:53
We almost take this for granted these days, but the idea with machine learning is that
7:57
rather than trying to explicitly define a procedure for how to do that task in code,
8:02
which is what people would have done in the earliest days of AI,
8:05
instead you set up a very flexible structure with tunable parameters,
8:09
like a bunch of knobs and dials, and then, somehow,
8:11
you use many examples of what the output should look like for a given input to tweak
8:16
and tune the values of those parameters to mimic this behavior.
8:19
For example, maybe the simplest form of machine learning is linear regression,
8:24
where your inputs and outputs are each single numbers,
8:27
something like the square footage of a house and its price,
8:30
and what you want is to find a line of best fit through this data, you know,
8:34
to predict future house prices.
8:37
That line is described by two continuous parameters,
8:40
say the slope and the y-intercept, and the goal of linear
8:43
regression is to determine those parameters to closely match the data.
8:48
Needless to say, deep learning models get much more complicated.
8:52
GPT-3, for example, has not two, but 175 billion parameters.
8:58
But here's the thing, it's not a given that you can create some giant
9:01
model with a huge number of parameters without it either grossly
9:05
overfitting the training data or being completely intractable to train.
9:10
Deep learning describes a class of models that in the
9:13
last couple decades have proven to scale remarkably well.
9:16
What unifies them is that they all use the same training algorithm,
9:19
it's called backpropagation, we talked about it in previous chapters,
9:22
and the context that I want you to have as we go in is that in order for this
9:26
training algorithm to work well at scale, these models have to follow a certain
9:30
specific format.
9:31
And if you know this format going in, it helps to explain many of the choices for how a
9:36
transformer processes language, which otherwise run the risk of feeling kinda arbitrary.
9:41
First, whatever kind of model you're making, the
9:43
input has to be formatted as an array of real numbers.
9:46
This could simply mean a list of numbers, it could be a two-dimensional array,
9:50
or very often you deal with higher dimensional arrays,
9:53
where the general term used is tensor.
9:56
You often think of that input data as being progressively transformed into many
10:00
distinct layers, where again, each layer is always structured as some kind of
10:04
array of real numbers, until you get to a final layer which you consider the output.
10:09
For example, the final layer in our text processing model is a list of numbers
10:13
representing the probability distribution for all possible next tokens.
10:17
In deep learning, these model parameters are almost always referred to as weights,
10:22
and this is because a key feature of these models is that the only way these
10:25
parameters interact with the data being processed is through weighted sums.
10:30
You also sprinkle some non-linear functions throughout,
10:32
but they won't depend on parameters.
10:35
Typically, though, instead of seeing the weighted sums all naked
10:38
and written out explicitly like this, you'll instead find them
10:41
packaged together as various components in a matrix vector product.
10:46
It amounts to saying the same thing, if you think back to how matrix vector
10:50
multiplication works, each component in the output looks like a weighted sum.
10:54
It's just often conceptually cleaner for you and me to think
10:58
about matrices that are filled with tunable parameters that
11:01
transform vectors that are drawn from the data being processed.
11:06
For example, those 175 billion weights in GPT-3 are
11:10
organized into just under 28,000 distinct matrices.
11:14
Those matrices in turn fall into eight different categories,
11:17
and what you and I are going to do is step through each one of those categories to
11:21
understand what that type does.
11:23
As we go through, I think it's kind of fun to reference the specific
11:27
numbers from GPT-3 to count up exactly where those 175 billion come from.
11:31
Even if nowadays there are bigger and better models,
11:34
this one has a certain charm as the first large-language
11:37
model to really capture the world's attention outside of ML communities.
11:41
Also, practically speaking, companies tend to keep much tighter
11:44
lips around the specific numbers for more modern networks.
11:47
I just want to set the scene going in, that as you peek under the
11:50
hood to see what happens inside a tool like ChatGPT,
11:53
almost all of the actual computation looks like matrix vector multiplication.
11:57
There's a little bit of a risk getting lost in the sea of billions of numbers,
12:01
but you should draw a very sharp distinction in your mind between
12:05
the weights of the model, which I'll always color in blue or red,
12:08
and the data being processed, which I'll always color in gray.
12:12
The weights are the actual brains, they are the things learned during training,
12:16
and they determine how it behaves.
12:18
The data being processed simply encodes whatever specific input is
12:22
fed into the model for a given run, like an example snippet of text.
Word embeddings
12:27
With all of that as foundation, let's dig into the first step of this text processing
12:31
example, which is to break up the input into little chunks and turn those chunks into
12:35
vectors.
12:37
I mentioned how those chunks are called tokens,
12:39
which might be pieces of words or punctuation,
12:41
but every now and then in this chapter and especially in the next one,
12:44
I'd like to just pretend that it's broken more cleanly into words.
12:48
Because we humans think in words, this will just make it much
12:51
easier to reference little examples and clarify each step.
12:55
The model has a predefined vocabulary, some list of all possible words,
12:59
say 50,000 of them, and the first matrix that we'll encounter,
13:03
known as the embedding matrix, has a single column for each one of these words.
13:08
These columns are what determines what vector each word turns into in that first step.
13:15
We label it W_E, and like all the matrices we see,
13:18
its values begin random, but they're going to be learned based on data.
13:23
Turning words into vectors was common practice in machine learning long before
13:27
transformers, but it's a little weird if you've never seen it before,
13:30
and it sets the foundation for everything that follows,
13:33
so let's take a moment to get familiar with it.
13:36
We often call this embedding a word, which invites you to think of these
13:39
vectors very geometrically as points in some high dimensional space.
13:44
Visualizing a list of three numbers as coordinates for points in 3D space would
13:48
be no problem, but word embeddings tend to be much much higher dimensional.
13:52
In GPT-3 they have 12,288 dimensions, and as you'll see,
13:55
it matters to work in a space that has a lot of distinct directions.
14:01
In the same way that you could take a two-dimensional slice through a 3D space
14:05
and project all the points onto that slice, for the sake of animating word
14:08
embeddings that a simple model is giving me, I'm going to do an analogous
14:12
thing by choosing a three-dimensional slice through this very high dimensional space,
14:16
and projecting the word vectors down onto that and displaying the results.
14:21
The big idea here is that as a model tweaks and tunes its weights to determine
14:25
how exactly words get embedded as vectors during training,
14:28
it tends to settle on a set of embeddings where directions in the space have a
14:33
kind of semantic meaning.
14:34
For the simple word-to-vector model I'm running here,
14:37
if I run a search for all the words whose embeddings are closest to that of tower,
14:42
you'll notice how they all seem to give very similar tower-ish vibes.
14:46
And if you want to pull up some Python and play along at home,
14:48
this is the specific model that I'm using to make the animations.
14:51
It's not a transformer, but it's enough to illustrate the
14:54
idea that directions in the space can carry semantic meaning.
14:58
A very classic example of this is how if you take the difference between
15:02
the vectors for woman and man, something you would visualize as a
15:05
little vector in the space connecting the tip of one to the tip of the other,
15:09
it's very similar to the difference between king and queen.
15:15
So let's say you didn't know the word for a female monarch,
15:18
you could find it by taking king, adding this woman minus man direction,
15:22
and searching for the embedding closest to that point.
15:27
At least, kind of.
15:28
Despite this being a classic example for the model I'm playing with,
15:31
the true embedding of queen is actually a little farther off than this would suggest,
15:35
presumably because the way queen is used in training data is not merely a feminine
15:39
version of king.
15:41
When I played around, family relations seemed to illustrate the idea much better.
15:46
The point is, it looks like during training the model found it advantageous to
15:50
choose embeddings such that one direction in this space encodes gender information.
15:56
Another example is that if you take the embedding of Italy,
16:00
and you subtract the embedding of Germany, and add that to the embedding of Hitler,
16:04
you get something very close to the embedding of Mussolini.
16:08
It's as if the model learned to associate some directions with Italian-ness,
16:13
and others with WWII axis leaders.
16:16
Maybe my favorite example in this vein is how in some models,
16:19
if you take the difference between Germany and Japan, and add it to sushi,
16:24
you end up very close to bratwurst.
16:27
Also in playing this game of finding nearest neighbors,
16:30
I was very pleased to see how close cat was to both beast and monster.
16:34
One bit of mathematical intuition that's helpful to have in mind,
16:37
especially for the next chapter, is how the dot product of two
16:40
vectors can be thought of as a way to measure how well they align.
16:44
Computationally, dot products involve multiplying all the
16:47
corresponding components and then adding the results, which is good,
16:51
since so much of our computation has to look like weighted sums.
16:55
Geometrically, the dot product is positive when vectors point in similar directions,
16:59
it's zero if they're perpendicular, and it's negative whenever
17:03
they point in opposite directions.
17:06
For example, let's say you were playing with this model,
17:09
and you hypothesize that the embedding of cats minus cat might represent a sort of
17:14
plurality direction in this space.
17:17
To test this, I'm going to take this vector and compute its dot
17:20
product against the embeddings of certain singular nouns,
17:23
and compare it to the dot products with the corresponding plural nouns.
17:27
If you play around with this, you'll notice that the plural ones
17:30
do indeed seem to consistently give higher values than the singular ones,
17:33
indicating that they align more with this direction.
17:37
It's also fun how if you take this dot product with the embeddings of the words one,
17:41
two, three, and so on, they give increasing values,
17:44
so it's as if we can quantitatively measure how plural the model finds a given word.
17:50
Again, the specifics for how words get embedded is learned using data.
17:54
This embedding matrix, whose columns tell us what happens to each word,
17:57
is the first pile of weights in our model.
18:00
Using the GPT-3 numbers, the vocabulary size specifically is 50,257,
18:04
and again, technically this consists not of words per se, but of tokens.
18:10
The embedding dimension is 12,288, and multiplying those
18:14
tells us this consists of about 617 million weights.
18:18
Let's go ahead and add this to a running tally,
18:20
remembering that by the end we should count up to 175 billion.
Embeddings beyond words
18:25
In the case of transformers, you really want to think of the vectors
18:28
in this embedding space as not merely representing individual words.
18:32
For one thing, they also encode information about the position of that word,
18:36
which we'll talk about later, but more importantly,
18:39
you should think of them as having the capacity to soak in context.
18:43
A vector that started its life as the embedding of the word king, for example,
18:47
might progressively get tugged and pulled by various blocks in this network,
18:51
so that by the end it points in a much more specific and nuanced direction that
18:55
somehow encodes that it was a king who lived in Scotland,
18:58
and who had achieved his post after murdering the previous king,
19:01
and who's being described in Shakespearean language.
19:05
Think about your own understanding of a given word.
19:08
The meaning of that word is clearly informed by the surroundings,
19:11
and sometimes this includes context from a long distance away,
19:15
so in putting together a model that has the ability to predict what word comes next,
19:19
the goal is to somehow empower it to incorporate context efficiently.
19:24
To be clear, in that very first step, when you create the array of
19:27
vectors based on the input text, each one of those is simply plucked
19:30
out of the embedding matrix, so initially each one can only encode
19:33
the meaning of a single word without any input from its surroundings.
19:37
But you should think of the primary goal of this network that it flows through
19:41
as being to enable each one of those vectors to soak up a meaning that's much
19:45
more rich and specific than what mere individual words could represent.
19:49
The network can only process a fixed number of vectors at a time,
19:52
known as its context size.
19:54
For GPT-3 it was trained with a context size of 2048,
19:57
so the data flowing through the network always looks like this array of 2048 columns,
20:02
each of which has 12,000 dimensions.
20:05
This context size limits how much text the transformer can
20:08
incorporate when it's making a prediction of the next word.
20:12
This is why long conversations with certain chatbots,
20:15
like the early versions of ChatGPT, often gave the feeling of
20:18
the bot kind of losing the thread of conversation as you continued too long.
Unembedding
20:23
We'll go into the details of attention in due time,
20:25
but skipping ahead I want to talk for a minute about what happens at the very end.
20:29
Remember, the desired output is a probability
20:31
distribution over all tokens that might come next.
20:35
For example, if the very last word is Professor,
20:37
and the context includes words like Harry Potter,
20:40
and immediately preceding we see least favorite teacher,
20:43
and also if you give me some leeway by letting me pretend that tokens simply
20:47
look like full words, then a well-trained network that had built up knowledge
20:51
of Harry Potter would presumably assign a high number to the word Snape.
20:56
This involves two different steps.
20:58
The first one is to use another matrix that maps the very last vector in that
21:03
context to a list of 50,000 values, one for each token in the vocabulary.
21:08
Then there's a function that normalizes this into a probability distribution,
21:12
it's called softmax and we'll talk more about it in just a second,
21:15
but before that it might seem a little bit weird to only use this last embedding
21:19
to make a prediction, when after all in that last step there are thousands of
21:23
other vectors in the layer just sitting there with their own context-rich meanings.
21:28
This has to do with the fact that in the training process it turns out to be
21:32
much more efficient if you use each one of those vectors in the final layer
21:36
to simultaneously make a prediction for what would come immediately after it.
21:40
There's a lot more to be said about training later on,
21:43
but I just want to call that out right now.
21:45
This matrix is called the Unembedding matrix and we give it the label WU.
21:50
Again, like all the weight matrices we see, its entries begin at random,
21:53
but they are learned during the training process.
21:56
Keeping score on our total parameter count, this Unembedding
21:59
matrix has one row for each word in the vocabulary,
22:02
and each row has the same number of elements as the embedding dimension.
22:06
It's very similar to the embedding matrix, just with the order swapped,
22:10
so it adds another 617 million parameters to the network,
22:13
meaning our count so far is a little over a billion,
22:16
a small but not wholly insignificant fraction of the 175 billion
22:20
we'll end up with in total.
Softmax with temperature
22:22
As the very last mini-lesson for this chapter,
22:24
I want to talk more about this softmax function,
22:26
since it makes another appearance for us once we dive into the attention blocks.
22:31
The idea is that if you want a sequence of numbers to act as a probability distribution,
22:36
say a distribution over all possible next words,
22:39
then each value has to be between 0 and 1, and you also need all of them to add up to 1.
22:45
However, if you're playing the deep learning game where everything you do looks like
22:49
matrix-vector multiplication, the outputs you get by default don't abide by this at all.
22:55
The values are often negative, or much bigger than 1,
22:57
and they almost certainly don't add up to 1.
23:00
Softmax is the standard way to turn an arbitrary list of numbers
23:04
into a valid distribution in such a way that the largest values end up closest to 1,
23:08
and the smaller values end up very close to 0.
23:11
That's all you really need to know.
23:13
But if you're curious, the way it works is to first raise e to the power
23:17
of each of the numbers, which means you now have a list of positive values,
23:21
and then you can take the sum of all those positive values and divide each
23:25
term by that sum, which normalizes it into a list that adds up to 1.
23:30
You'll notice that if one of the numbers in the input is meaningfully bigger than the
23:34
rest, then in the output the corresponding term dominates the distribution,
23:37
so if you were sampling from it you'd almost certainly just be picking the maximizing
23:42
input.
23:42
But it's softer than just picking the max in the sense that when other values
23:46
are similarly large, they also get meaningful weight in the distribution,
23:50
and everything changes continuously as you continuously vary the inputs.
23:55
In some situations, like when ChatGPT is using this distribution to create a next word,
23:59
there's room for a little bit of extra fun by adding a little extra spice into this
24:04
function, with a constant T thrown into the denominator of those exponents.
24:09
We call it the temperature, since it vaguely resembles the role of temperature in
24:14
certain thermodynamics equations, and the effect is that when T is larger,
24:18
you give more weight to the lower values, meaning the distribution is a little bit
24:22
more uniform, and if T is smaller, then the bigger values will dominate more
24:26
aggressively, where in the extreme, setting T equal to zero means all of the weight
24:31
goes to maximum value.
24:33
For example, I'll have GPT-3 generate a story with the seed text,
24:37
"once upon a time there was A", but I'll use different temperatures in each case.
24:43
Temperature zero means that it always goes with the most predictable word,
24:48
and what you get ends up being a trite derivative of Goldilocks.
24:53
A higher temperature gives it a chance to choose less likely words,
24:56
but it comes with a risk.
24:58
In this case, the story starts out more originally,
25:01
about a young web artist from South Korea, but it quickly degenerates into nonsense.
25:06
Technically speaking, the API doesn't actually let you pick a temperature bigger than 2.
25:11
There's no mathematical reason for this, it's just an arbitrary constraint imposed
25:15
to keep their tool from being seen generating things that are too nonsensical.
25:19
So if you're curious, the way this animation is actually working is I'm taking the
25:24
20 most probable next tokens that GPT-3 generates,
25:27
which seems to be the maximum they'll give me,
25:29
and then I tweak the probabilities based on an exponent of 1/5.
25:33
As another bit of jargon, in the same way that you might call the components of
25:37
the output of this function probabilities, people often refer to the inputs as logits,
25:42
or some people say logits, some people say logits, I'm gonna say logits.
25:46
So for instance, when you feed in some text, you have all these word embeddings
25:50
flow through the network, and you do this final multiplication with the
25:53
unembedding matrix, machine learning people would refer to the components in that raw,
25:58
unnormalized output as the logits for the next word prediction.
Up next
26:03
A lot of the goal with this chapter was to lay the foundations for
26:06
understanding the attention mechanism, Karate Kid wax-on-wax-off style.
26:10
You see, if you have a strong intuition for word embeddings, for softmax,
26:14
for how dot products measure similarity, and also the underlying premise that
26:19
most of the calculations have to look like matrix multiplication with matrices
26:23
full of tunable parameters, then understanding the attention mechanism,
26:27
this cornerstone piece in the whole modern boom in AI, should be relatively smooth.
26:32
For that, come join me in the next chapter.
26:36
As I'm publishing this, a draft of that next chapter
26:38
is available for review by Patreon supporters.
26:41
A final version should be up in public in a week or two,
26:44
it usually depends on how much I end up changing based on that review.
26:47
In the meantime, if you want to dive into attention,
26:49
and if you want to help the channel out a little bit, it's there waiting.

-----

Attention in transformers, step-by-step | Deep Learning Chapter 6

Timestamps:
0:00 - Recap on embeddings
1:39 - Motivating examples
4:29 - The attention pattern
11:08 - Masking
12:42 - Context size
13:10 - Values
15:44 - Counting parameters
18:21 - Cross-attention
19:19 - Multiple heads
22:16 - The output matrix
23:19 - Going deeper
24:54 - Ending


0:00
In the last chapter, you and I started to step
0:01
through the internal workings of a transformer.
0:04
This is one of the key pieces of technology inside large language models,
0:07
and a lot of other tools in the modern wave of AI.
0:10
It first hit the scene in a now-famous 2017 paper called Attention is All You Need,
0:15
and in this chapter you and I will dig into what this attention mechanism is,
0:19
visualizing how it processes data.
0:26
As a quick recap, here's the important context I want you to have in mind.
0:30
The goal of the model that you and I are studying is to
0:32
take in a piece of text and predict what word comes next.
0:36
The input text is broken up into little pieces that we call tokens,
0:40
and these are very often words or pieces of words,
0:42
but just to make the examples in this video easier for you and me to think about,
0:47
let's simplify by pretending that tokens are always just words.
0:51
The first step in a transformer is to associate each token
0:54
with a high-dimensional vector, what we call its embedding.
0:57
The most important idea I want you to have in mind is how directions in this
1:02
high-dimensional space of all possible embeddings can correspond with semantic meaning.
1:07
In the last chapter we saw an example for how direction can correspond to gender,
1:11
in the sense that adding a certain step in this space can take you from the
1:15
embedding of a masculine noun to the embedding of the corresponding feminine noun.
1:20
That's just one example you could imagine how many other directions in this
1:23
high-dimensional space could correspond to numerous other aspects of a word's meaning.
1:28
The aim of a transformer is to progressively adjust these embeddings
1:32
so that they don't merely encode an individual word,
1:35
but instead they bake in some much, much richer contextual meaning.
Motivating examples
1:40
I should say up front that a lot of people find the attention mechanism,
1:43
this key piece in a transformer, very confusing,
1:46
so don't worry if it takes some time for things to sink in.
1:49
I think that before we dive into the computational details and all
1:52
the matrix multiplications, it's worth thinking about a couple
1:55
examples for the kind of behavior that we want attention to enable.
2:00
Consider the phrases American shrew mole, one mole of carbon dioxide,
2:04
and take a biopsy of the mole.
2:06
You and I know that the word mole has different meanings in each one of these,
2:09
based on the context.
2:11
But after the first step of a transformer, the one that breaks up the text
2:15
and associates each token with a vector, the vector that's associated with
2:18
mole would be the same in all of these cases,
2:21
because this initial token embedding is effectively a lookup table with no
2:24
reference to the context.
2:26
It's only in the next step of the transformer that the surrounding
2:29
embeddings have the chance to pass information into this one.
2:33
The picture you might have in mind is that there are multiple distinct directions in
2:38
this embedding space encoding the multiple distinct meanings of the word mole,
2:42
and that a well-trained attention block calculates what you need to add to the generic
2:47
embedding to move it to one of these specific directions, as a function of the context.
2:53
To take another example, consider the embedding of the word tower.
2:57
This is presumably some very generic, non-specific direction in the space,
3:01
associated with lots of other large, tall nouns.
3:04
If this word was immediately preceded by Eiffel,
3:06
you could imagine wanting the mechanism to update this vector so that
3:10
it points in a direction that more specifically encodes the Eiffel tower,
3:14
maybe correlated with vectors associated with Paris and France and things made of steel.
3:19
If it was also preceded by the word miniature,
3:22
then the vector should be updated even further,
3:24
so that it no longer correlates with large, tall things.
3:29
More generally than just refining the meaning of a word,
3:32
the attention block allows the model to move information encoded in
3:35
one embedding to that of another, potentially ones that are quite far away,
3:39
and potentially with information that's much richer than just a single word.
3:43
What we saw in the last chapter was how after all of the vectors flow through the
3:47
network, including many different attention blocks,
3:50
the computation you perform to produce a prediction of the next token is entirely a
3:55
function of the last vector in the sequence.
3:59
Imagine, for example, that the text you input is most of an entire mystery novel,
4:03
all the way up to a point near the end, which reads, therefore the murderer was.
4:08
If the model is going to accurately predict the next word,
4:11
that final vector in the sequence, which began its life simply embedding the word was,
4:16
will have to have been updated by all of the attention blocks to represent much,
4:20
much more than any individual word, somehow encoding all of the information
4:24
from the full context window that's relevant to predicting the next word.
The attention pattern
4:29
To step through the computations, though, let's take a much simpler example.
4:32
Imagine that the input includes the phrase, a
4:35
fluffy blue creature roamed the verdant forest.
4:38
And for the moment, suppose that the only type of update that we care about
4:42
is having the adjectives adjust the meanings of their corresponding nouns.
4:47
What I'm about to describe is what we would call a single head of attention,
4:50
and later we will see how the attention block consists of many different heads run in
4:54
parallel.
4:56
Again, the initial embedding for each word is some high dimensional vector
4:59
that only encodes the meaning of that particular word with no context.
5:04
Actually, that's not quite true.
5:05
They also encode the position of the word.
5:07
There's a lot more to say about the specific way that positions are encoded,
5:11
but right now, all you need to know is that the entries of this vector are
5:15
enough to tell you both what the word is and where it exists in the context.
5:19
Let's go ahead and denote these embeddings with the letter e.
5:22
The goal is to have a series of computations produce a new refined
5:26
set of embeddings where, for example, those corresponding to the
5:29
nouns have ingested the meaning from their corresponding adjectives.
5:33
And playing the deep learning game, we want most of the computations
5:37
involved to look like matrix-vector products,
5:39
where the matrices are full of tuneable weights,
5:41
things that the model will learn based on data.
5:44
To be clear, I'm making up this example of adjectives updating nouns just to
5:48
illustrate the type of behavior that you could imagine an attention head doing.
5:52
As with so much deep learning, the true behavior is much harder to parse because it's
5:57
based on tweaking and tuning a huge number of parameters to minimize some cost function.
6:01
It's just that as we step through all of different matrices filled with parameters
6:05
that are involved in this process, I think it's really helpful to have an imagined
6:09
example of something that it could be doing to help keep it all more concrete.
6:14
For the first step of this process, you might imagine each noun, like creature,
6:18
asking the question, hey, are there any adjectives sitting in front of me?
6:22
And for the words fluffy and blue, to each be able to answer,
6:25
yeah, I'm an adjective and I'm in that position.
6:28
That question is somehow encoded as yet another vector,
6:32
another list of numbers, which we call the query for this word.
6:36
This query vector though has a much smaller dimension than the embedding vector, say 128.
6:42
Computing this query looks like taking a certain matrix,
6:46
which I'll label wq, and multiplying it by the embedding.
6:50
Compressing things a bit, let's write that query vector as q,
6:54
and then anytime you see me put a matrix next to an arrow like this one,
6:58
it's meant to represent that multiplying this matrix by the vector at the arrow's start
7:02
gives you the vector at the arrow's end.
7:05
In this case, you multiply this matrix by all of the embeddings in the context,
7:10
producing one query vector for each token.
7:13
The entries of this matrix are parameters of the model,
7:16
which means the true behavior is learned from data, and in practice,
7:19
what this matrix does in a particular attention head is challenging to parse.
7:23
But for our sake, imagining an example that we might hope that it would learn,
7:27
we'll suppose that this query matrix maps the embeddings of nouns to
7:31
certain directions in this smaller query space that somehow encodes
7:34
the notion of looking for adjectives in preceding positions.
7:38
As to what it does to other embeddings, who knows?
7:41
Maybe it simultaneously tries to accomplish some other goal with those.
7:44
Right now, we're laser focused on the nouns.
7:47
At the same time, associated with this is a second matrix called the key matrix,
7:51
which you also multiply by every one of the embeddings.
7:55
This produces a second sequence of vectors that we call the keys.
7:59
Conceptually, you want to think of the keys as potentially answering the queries.
8:03
This key matrix is also full of tuneable parameters, and just like the query matrix,
8:07
it maps the embedding vectors to that same smaller dimensional space.
8:12
You think of the keys as matching the queries whenever they closely align with each other.
8:17
In our example, you would imagine that the key matrix maps the adjectives like fluffy and
8:22
blue to vectors that are closely aligned with the query produced by the word creature.
8:27
To measure how well each key matches each query,
8:30
you compute a dot product between each possible key-query pair.
8:34
I like to visualize a grid full of a bunch of dots,
8:37
where the bigger dots correspond to the larger dot products,
8:40
the places where the keys and queries align.
8:43
For our adjective noun example, that would look a little more like this,
8:47
where if the keys produced by fluffy and blue really do align closely with the query
8:52
produced by creature, then the dot products in these two spots would be some large
8:57
positive numbers.
8:59
In the lingo, machine learning people would say that this means the
9:02
embeddings of fluffy and blue attend to the embedding of creature.
9:06
By contrast to the dot product between the key for some other
9:09
word like the and the query for creature would be some small
9:12
or negative value that reflects that are unrelated to each other.
9:17
So we have this grid of values that can be any real number from
9:21
negative infinity to infinity, giving us a score for how relevant
9:25
each word is to updating the meaning of every other word.
9:29
The way we're about to use these scores is to take a certain
9:32
weighted sum along each column, weighted by the relevance.
9:36
So instead of having values range from negative infinity to infinity,
9:40
what we want is for the numbers in these columns to be between 0 and 1,
9:43
and for each column to add up to 1, as if they were a probability distribution.
9:49
If you're coming in from the last chapter, you know what we need to do then.
9:52
We compute a softmax along each one of these columns to normalize the values.
10:00
In our picture, after you apply softmax to all of the columns,
10:03
we'll fill in the grid with these normalized values.
10:06
At this point you're safe to think about each column as giving weights according
10:10
to how relevant the word on the left is to the corresponding value at the top.
10:15
We call this grid an attention pattern.
10:18
Now if you look at the original transformer paper,
10:20
there's a really compact way that they write this all down.
10:23
Here the variables q and k represent the full arrays of query
10:27
and key vectors respectively, those little vectors you get by
10:31
multiplying the embeddings by the query and the key matrices.
10:35
This expression up in the numerator is a really compact way to represent
10:39
the grid of all possible dot products between pairs of keys and queries.
10:44
A small technical detail that I didn't mention is that for numerical stability,
10:48
it happens to be helpful to divide all of these values by the
10:51
square root of the dimension in that key query space.
10:54
Then this softmax that's wrapped around the full expression
10:57
is meant to be understood to apply column by column.
11:01
As to that v term, we'll talk about it in just a second.
11:05
Before that, there's one other technical detail that so far I've skipped.
Masking
11:09
During the training process, when you run this model on a given text example,
11:12
and all of the weights are slightly adjusted and tuned to either reward or punish it
11:17
based on how high a probability it assigns to the true next word in the passage,
11:21
it turns out to make the whole training process a lot more efficient if you
11:25
simultaneously have it predict every possible next token following each initial
11:29
subsequence of tokens in this passage.
11:31
For example, with the phrase that we've been focusing on,
11:34
it might also be predicting what words follow creature and what words follow the.
11:39
This is really nice, because it means what would otherwise
11:42
be a single training example effectively acts as many.
11:46
For the purposes of our attention pattern, it means that you never
11:49
want to allow later words to influence earlier words,
11:52
since otherwise they could kind of give away the answer for what comes next.
11:56
What this means is that we want all of these spots here,
11:59
the ones representing later tokens influencing earlier ones,
12:02
to somehow be forced to be zero.
12:05
The simplest thing you might think to do is to set them equal to zero,
12:08
but if you did that the columns wouldn't add up to one anymore,
12:11
they wouldn't be normalized.
12:13
So instead, a common way to do this is that before applying softmax,
12:16
you set all of those entries to be negative infinity.
12:19
If you do that, then after applying softmax, all of those get turned into zero,
12:23
but the columns stay normalized.
12:26
This process is called masking.
12:27
There are versions of attention where you don't apply it, but in our GPT example,
12:31
even though this is more relevant during the training phase than it would be,
12:34
say, running it as a chatbot or something like that,
12:37
you do always apply this masking to prevent later tokens from influencing earlier ones.
Context size
12:42
Another fact that's worth reflecting on about this attention
12:45
pattern is how its size is equal to the square of the context size.
12:49
So this is why context size can be a really huge bottleneck for large language models,
12:53
and scaling it up is non-trivial.
12:56
As you imagine, motivated by a desire for bigger and bigger context windows,
13:00
recent years have seen some variations to the attention mechanism aimed at making
13:04
context more scalable, but right here, you and I are staying focused on the basics.
Values
13:10
Okay, great, computing this pattern lets the model
13:12
deduce which words are relevant to which other words.
13:16
Now you need to actually update the embeddings,
13:18
allowing words to pass information to whichever other words they're relevant to.
13:22
For example, you want the embedding of Fluffy to somehow cause a change
13:26
to Creature that moves it to a different part of this 12,000-dimensional
13:30
embedding space that more specifically encodes a Fluffy creature.
13:35
What I'm going to do here is first show you the most straightforward
13:38
way that you could do this, though there's a slight way that
13:40
this gets modified in the context of multi-headed attention.
13:44
This most straightforward way would be to use a third matrix,
13:47
what we call the value matrix, which you multiply by the embedding of that first word,
13:51
for example Fluffy.
13:53
The result of this is what you would call a value vector,
13:55
and this is something that you add to the embedding of the second word,
13:59
in this case something you add to the embedding of Creature.
14:02
So this value vector lives in the same very high-dimensional space as the embeddings.
14:07
When you multiply this value matrix by the embedding of a word,
14:10
you might think of it as saying, if this word is relevant to adjusting the meaning of
14:15
something else, what exactly should be added to the embedding of that something else
14:19
in order to reflect this?
14:22
Looking back in our diagram, let's set aside all of the keys and the queries,
14:25
since after you compute the attention pattern you're done with those,
14:29
then you're going to take this value matrix and multiply it by every
14:32
one of those embeddings to produce a sequence of value vectors.
14:37
You might think of these value vectors as being
14:39
kind of associated with the corresponding keys.
14:42
For each column in this diagram, you multiply each of the
14:45
value vectors by the corresponding weight in that column.
14:50
For example here, under the embedding of Creature,
14:52
you would be adding large proportions of the value vectors for Fluffy and Blue,
14:57
while all of the other value vectors get zeroed out, or at least nearly zeroed out.
15:02
And then finally, the way to actually update the embedding associated with this column,
15:06
previously encoding some context-free meaning of Creature,
15:09
you add together all of these rescaled values in the column,
15:13
producing a change that you want to add, that I'll label delta-e,
15:16
and then you add that to the original embedding.
15:19
Hopefully what results is a more refined vector encoding the more
15:23
contextually rich meaning, like that of a fluffy blue creature.
15:27
And of course you don't just do this to one embedding,
15:30
you apply the same weighted sum across all of the columns in this picture,
15:34
producing a sequence of changes, adding all of those changes to the corresponding
15:38
embeddings, produces a full sequence of more refined embeddings popping out
15:42
of the attention block.
Counting parameters
15:44
Zooming out, this whole process is what you would describe as a single head of attention.
15:49
As I've described things so far, this process is parameterized by three distinct
15:54
matrices, all filled with tunable parameters, the key, the query, and the value.
15:59
I want to take a moment to continue what we started in the last chapter,
16:02
with the scorekeeping where we count up the total number of model parameters using the
16:07
numbers from GPT-3.
16:09
These key and query matrices each have 12,288 columns, matching the embedding dimension,
16:15
and 128 rows, matching the dimension of that smaller key query space.
16:20
This gives us an additional 1.5 million or so parameters for each one.
16:24
If you look at that value matrix by contrast, the way I've described things so
16:30
far would suggest that it's a square matrix that has 12,288 columns and 12,288 rows,
16:35
since both its inputs and outputs live in this very large embedding space.
16:41
If true, that would mean about 150 million added parameters.
16:45
And to be clear, you could do that.
16:47
You could devote orders of magnitude more parameters
16:49
to the value map than to the key and query.
16:52
But in practice, it is much more efficient if instead you make
16:54
it so that the number of parameters devoted to this value map
16:57
is the same as the number devoted to the key and the query.
17:01
This is especially relevant in the setting of
17:03
running multiple attention heads in parallel.
17:06
The way this looks is that the value map is factored as a product of two smaller matrices.
17:11
Conceptually, I would still encourage you to think about the overall linear map,
17:15
one with inputs and outputs, both in this larger embedding space,
17:18
for example taking the embedding of blue to this blueness direction that you would
17:23
add to nouns.
17:27
The first matrix on the right here has a smaller number of rows,
17:30
typically the same size as the key-query space
17:33
What this means is you can think of it as mapping the
17:35
large embedding vectors down to a much smaller space.
17:39
This is not the conventional naming, but I'm going to call this the value down matrix.
17:43
The second matrix maps from this smaller space back up to the embedding space,
17:47
producing the vectors that you use to make the actual updates.
17:51
I'm going to call this one the value up matrix, which again is not conventional.
17:55
The way that you would see this written in most papers looks a little different.
17:58
I'll talk about it in a minute.
17:59
In my opinion, it tends to make things a little more conceptually confusing.
18:03
To throw in linear algebra jargon here, what we're basically doing is
18:06
constraining the overall value map to be a low rank transformation.
18:11
Turning back to the parameter count, all four of these matrices have the same size,
18:16
and adding them all up we get about 6.3 million parameters for one attention head.
Cross-attention
18:22
As a quick side note, to be a little more accurate,
18:24
everything described so far is what people would call a self-attention head,
18:27
to distinguish it from a variation that comes up in other models that's
18:30
called cross-attention.
18:32
This isn't relevant to our GPT example, but if you're curious,
18:35
cross-attention involves models that process two distinct types of data,
18:39
like text in one language and text in another language that's part of an
18:43
ongoing generation of a translation, or maybe audio input of speech and an
18:47
ongoing transcription.
18:50
A cross-attention head looks almost identical.
18:52
The only difference is that the key and query maps act on different data sets.
18:57
In a model doing translation, for example, the keys might come from one language,
19:02
while the queries come from another, and the attention pattern could describe
19:06
which words from one language correspond to which words in another.
19:10
And in this setting there would typically be no masking,
19:12
since there's not really any notion of later tokens affecting earlier ones.
19:17
Staying focused on self-attention though, if you understood everything so far,
Multiple heads
19:20
and if you were to stop here, you would come away with the essence of what attention
19:24
really is.
19:25
All that's really left to us is to lay out the sense
19:28
in which you do this many many different times.
19:32
In our central example we focused on adjectives updating nouns,
19:35
but of course there are lots of different ways that context can influence the
19:38
meaning of a word.
19:40
If the words they crashed the preceded the word car,
19:43
it has implications for the shape and structure of that car.
19:47
And a lot of associations might be less grammatical.
19:49
If the word wizard is anywhere in the same passage as Harry,
19:52
it suggests that this might be referring to Harry Potter,
19:55
whereas if instead the words Queen, Sussex, and William were in that passage,
19:59
then perhaps the embedding of Harry should instead be updated to refer to the prince.
20:05
For every different type of contextual updating that you might imagine,
20:08
the parameters of these key and query matrices would be different to
20:11
capture the different attention patterns, and the parameters of our
20:15
value map would be different based on what should be added to the embeddings.
20:19
And again, in practice the true behavior of these maps is much more
20:23
difficult to interpret, where the weights are set to do whatever the
20:26
model needs them to do to best accomplish its goal of predicting the next token.
20:31
As I said before, everything we described is a single head of attention,
20:35
and a full attention block inside a transformer consists of what's
20:38
called multi-headed attention, where you run a lot of these operations in parallel,
20:43
each with its own distinct key query and value maps.
20:47
GPT-3 for example uses 96 attention heads inside each block.
20:52
Considering that each one is already a bit confusing,
20:54
it's certainly a lot to hold in your head.
20:56
Just to spell it all out very explicitly, this means you have 96 distinct
21:01
key and query matrices producing 96 distinct attention patterns.
21:05
Then each head has its own distinct value matrices
21:08
used to produce 96 sequences of value vectors.
21:12
These are all added together using the corresponding attention patterns as weights.
21:17
What this means is that for each position in the context, each token,
21:21
every one of these heads produces a proposed change to be added to the embedding in
21:26
that position.
21:27
So what you do is you sum together all of those proposed changes, one for each head,
21:32
and you add the result to the original embedding of that position.
21:36
This entire sum here would be one slice of what's outputted from this multi-headed
21:41
attention block, a single one of those refined embeddings that pops out the other end
21:47
of it.
21:48
Again, this is a lot to think about, so don't
21:50
worry at all if it takes some time to sink in.
21:52
The overall idea is that by running many distinct heads in parallel,
21:56
you're giving the model the capacity to learn many distinct ways that context
22:00
changes meaning.
22:03
Pulling up our running tally for parameter count with 96 heads,
22:07
each including its own variation of these four matrices,
22:10
each block of multi-headed attention ends up with around 600 million parameters.
The output matrix
22:16
There's one added slightly annoying thing that I should really
22:19
mention for any of you who go on to read more about transformers.
22:22
You remember how I said that the value map is factored out into these two
22:25
distinct matrices, which I labeled as the value down and the value up matrices.
22:29
The way that I framed things would suggest that you see this pair of matrices
22:34
inside each attention head, and you could absolutely implement it this way.
22:38
That would be a valid design.
22:40
But the way that you see this written in papers and the way
22:42
that it's implemented in practice looks a little different.
22:45
All of these value up matrices for each head appear stapled together in one giant matrix
22:50
that we call the output matrix, associated with the entire multi-headed attention block.
22:56
And when you see people refer to the value matrix for a given attention head,
23:00
they're typically only referring to this first step,
23:03
the one that I was labeling as the value down projection into the smaller space.
23:08
For the curious among you, I've left an on-screen note about it.
23:11
It's one of those details that runs the risk of distracting
23:13
from the main conceptual points, but I do want to call it out
23:16
just so that you know if you read about this in other sources.
Going deeper
23:19
Setting aside all the technical nuances, in the preview from the last chapter we saw how
23:23
data flowing through a transformer doesn't just flow through a single attention block.
23:28
For one thing, it also goes through these other operations called multi-layer perceptrons.
23:33
We'll talk more about those in the next chapter.
23:35
And then it repeatedly goes through many many copies of both of these operations.
23:39
What this means is that after a given word imbibes some of its context,
23:43
there are many more chances for this more nuanced embedding
23:47
to be influenced by its more nuanced surroundings.
23:50
The further down the network you go, with each embedding taking in more and more
23:54
meaning from all the other embeddings, which themselves are getting more and more
23:59
nuanced, the hope is that there's the capacity to encode higher level and more
24:03
abstract ideas about a given input beyond just descriptors and grammatical structure.
24:07
Things like sentiment and tone and whether it's a poem and what underlying
24:11
scientific truths are relevant to the piece and things like that.
24:16
Turning back one more time to our scorekeeping, GPT-3 includes 96 distinct layers,
24:21
so the total number of key query and value parameters is multiplied by another 96,
24:27
which brings the total sum to just under 58 billion distinct parameters
24:31
devoted to all of the attention heads.
24:34
That is a lot to be sure, but it's only about a third
24:37
of the 175 billion that are in the network in total.
24:41
So even though attention gets all of the attention,
24:44
the majority of parameters come from the blocks sitting in between these steps.
24:48
In the next chapter, you and I will talk more about those
24:50
other blocks and also a lot more about the training process.
Ending
24:54
A big part of the story for the success of the attention mechanism is not so much any
24:58
specific kind of behaviour that it enables, but the fact that it's extremely
25:02
parallelizable, meaning that you can run a huge number of computations in a short time
25:07
using GPUs.
25:09
Given that one of the big lessons about deep learning in the last decade or two has
25:13
been that scale alone seems to give huge qualitative improvements in model performance,
25:17
there's a huge advantage to parallelizable architectures that let you do this.
25:22
If you want to learn more about this stuff, I've left lots of links in the description.
25:25
In particular, anything produced by Andrej Karpathy or Chris Ola tend to be pure gold.
25:30
In this video, I wanted to just jump into attention in its current form,
25:33
but if you're curious about more of the history for how we got here
25:36
and how you might reinvent this idea for yourself,
25:38
my friend Vivek just put up a couple videos giving a lot more of that motivation.
25:43
Also, Britt Cruz from the channel The Art of the Problem has a
25:45
really nice video about the history of large language models.
26:04
Thank you.

----
How might LLMs store facts | Deep Learning Chapter 7

Sections:
0:00 - Where facts in LLMs live
2:15 - Quick refresher on transformers
4:39 - Assumptions for our toy example
6:07 - Inside a multilayer perceptron
15:38 - Counting parameters
17:04 - Superposition
21:37 - Up next


Where facts in LLMs live
0:00
If you feed a large language model the phrase, Michael Jordan plays the sport of blank,
0:05
and you have it predict what comes next, and it correctly predicts basketball,
0:09
this would suggest that somewhere, inside its hundreds of billions of parameters,
0:14
it's baked in knowledge about a specific person and his specific sport.
0:18
And I think in general, anyone who's played around with one of these
0:22
models has the clear sense that it's memorized tons and tons of facts.
0:25
So a reasonable question you could ask is, how exactly does that work?
0:29
And where do those facts live?
0:35
Last December, a few researchers from Google DeepMind posted about work on this question,
0:40
and they were using this specific example of matching athletes to their sports.
0:44
And although a full mechanistic understanding of how facts are stored remains unsolved,
0:49
they had some interesting partial results, including the very general high-level
0:54
conclusion that the facts seem to live inside a specific part of these networks,
0:58
known fancifully as the multi-layer perceptrons, or MLPs for short.
1:03
In the last couple of chapters, you and I have been digging into
1:06
the details behind transformers, the architecture underlying large language models,
1:10
and also underlying a lot of other modern AI.
1:13
In the most recent chapter, we were focusing on a piece called Attention.
1:16
And the next step for you and me is to dig into the details of what happens inside
1:20
these multi-layer perceptrons, which make up the other big portion of the network.
1:25
The computation here is actually relatively simple,
1:28
especially when you compare it to attention.
1:30
It boils down essentially to a pair of matrix
1:32
multiplications with a simple something in between.
1:35
However, interpreting what these computations are doing is exceedingly challenging.
1:41
Our main goal here is to step through the computations and make them memorable,
1:45
but I'd like to do it in the context of showing a specific example of how
1:49
one of these blocks could, at least in principle, store a concrete fact.
1:53
Specifically, it'll be storing the fact that Michael Jordan plays basketball.
1:58
I should mention the layout here is inspired by a conversation
2:00
I had with one of those DeepMind researchers, Neil Nanda.
2:04
For the most part, I will assume that you've either watched the last two chapters,
2:08
or otherwise you have a basic sense for what a transformer is,
2:11
but refreshers never hurt, so here's the quick reminder of the overall flow.
Quick refresher on transformers
2:15
You and I have been studying a model that's trained
2:18
to take in a piece of text and predict what comes next.
2:21
That input text is first broken into a bunch of tokens,
2:24
which means little chunks that are typically words or little pieces of words,
2:29
and each token is associated with a high-dimensional vector,
2:33
which is to say a long list of numbers.
2:35
This sequence of vectors then repeatedly passes through two kinds of operation,
2:40
attention, which allows the vectors to pass information between one another,
2:44
and then the multilayer perceptrons, the thing that we're gonna dig into today,
2:49
and also there's a certain normalization step in between.
2:53
After the sequence of vectors has flowed through many,
2:56
many different iterations of both of these blocks, by the end,
3:00
the hope is that each vector has soaked up enough information, both from the context,
3:04
all of the other words in the input, and also from the general knowledge that
3:09
was baked into the model weights through training,
3:12
that it can be used to make a prediction of what token comes next.
3:16
One of the key ideas that I want you to have in your mind is that all of
3:20
these vectors live in a very, very high-dimensional space,
3:23
and when you think about that space, different directions can encode different
3:27
kinds of meaning.
3:30
So a very classic example that I like to refer back to is how if you look
3:34
at the embedding of woman and subtract the embedding of man,
3:37
and you take that little step and you add it to another masculine noun,
3:41
something like uncle, you land somewhere very,
3:43
very close to the corresponding feminine noun.
3:46
In this sense, this particular direction encodes gender information.
3:51
The idea is that many other distinct directions in this super high-dimensional
3:55
space could correspond to other features that the model might want to represent.
4:01
In a transformer, these vectors don't merely encode the meaning of a single word, though.
4:06
As they flow through the network, they imbibe a much richer meaning based
4:10
on all the context around them, and also based on the model's knowledge.
4:15
Ultimately, each one needs to encode something far,
4:18
far beyond the meaning of a single word, since it needs to be sufficient to
4:22
predict what will come next.
4:24
We've already seen how attention blocks let you incorporate context,
4:28
but a majority of the model parameters actually live inside the MLP blocks,
4:32
and one thought for what they might be doing is that they offer extra capacity
4:37
to store facts.
4:38
Like I said, the lesson here is gonna center on the concrete toy example
Assumptions for our toy example
4:42
of how exactly it could store the fact that Michael Jordan plays basketball.
4:47
Now, this toy example is gonna require that you and I make
4:49
a couple of assumptions about that high-dimensional space.
4:52
First, we'll suppose that one of the directions represents the idea of a first name
4:56
Michael, and then another nearly perpendicular direction represents the idea of the
5:01
last name Jordan, and then yet a third direction will represent the idea of basketball.
5:07
So specifically, what I mean by this is if you look in the network and
5:11
you pluck out one of the vectors being processed,
5:13
if its dot product with this first name Michael direction is one,
5:17
that's what it would mean for the vector to be encoding the idea of a
5:20
person with that first name.
5:23
Otherwise, that dot product would be zero or negative,
5:26
meaning the vector doesn't really align with that direction.
5:29
And for simplicity, let's completely ignore the very reasonable
5:32
question of what it might mean if that dot product was bigger than one.
5:36
Similarly, its dot product with these other directions would
5:39
tell you whether it represents the last name Jordan or basketball.
5:44
So let's say a vector is meant to represent the full name, Michael Jordan,
5:48
then its dot product with both of these directions would have to be one.
5:53
Since the text Michael Jordan spans two different tokens,
5:56
this would also mean we have to assume that an earlier attention block has successfully
6:01
passed information to the second of these two vectors so as to ensure that it can
6:05
encode both names.
Inside a multilayer perceptron
6:07
With all of those as the assumptions, let's now dive into the meat of the lesson.
6:11
What happens inside a multilayer perceptron?
6:17
You might think of this sequence of vectors flowing into the block, and remember,
6:21
each vector was originally associated with one of the tokens from the input text.
6:26
What's gonna happen is that each individual vector from that sequence
6:29
goes through a short series of operations, we'll unpack them in just a moment,
6:33
and at the end, we'll get another vector with the same dimension.
6:36
That other vector is gonna get added to the original one that flowed in,
6:40
and that sum is the result flowing out.
6:43
This sequence of operations is something you apply to every vector in the sequence,
6:47
associated with every token in the input, and it all happens in parallel.
6:52
In particular, the vectors don't talk to each other in this step,
6:54
they're all kind of doing their own thing.
6:56
And for you and me, that actually makes it a lot simpler,
6:59
because it means if we understand what happens to just one of the
7:02
vectors through this block, we effectively understand what happens to all of them.
7:07
When I say this block is gonna encode the fact that Michael Jordan plays basketball,
7:11
what I mean is that if a vector flows in that encodes first name Michael and last
7:15
name Jordan, then this sequence of computations will produce something that includes
7:19
that direction basketball, which is what will add on to the vector in that position.
7:25
The first step of this process looks like multiplying that vector by a very big matrix.
7:30
No surprises there, this is deep learning.
7:32
And this matrix, like all of the other ones we've seen,
7:35
is filled with model parameters that are learned from data,
7:37
which you might think of as a bunch of knobs and dials that get tweaked and
7:41
tuned to determine what the model behavior is.
7:44
Now, one nice way to think about matrix multiplication is to imagine each row of
7:48
that matrix as being its own vector, and taking a bunch of dot products between
7:52
those rows and the vector being processed, which I'll label as E for embedding.
7:57
For example, suppose that very first row happened to equal
8:00
this first name Michael direction that we're presuming exists.
8:04
That would mean that the first component in this output, this dot product right here,
8:09
would be one if that vector encodes the first name Michael,
8:12
and zero or negative otherwise.
8:15
Even more fun, take a moment to think about what it would mean if that
8:19
first row was this first name Michael plus last name Jordan direction.
8:23
And for simplicity, let me go ahead and write that down as M plus J.
8:28
Then, taking a dot product with this embedding E,
8:30
things distribute really nicely, so it looks like M dot E plus J dot E.
8:34
And notice how that means the ultimate value would be two if the vector encodes the
8:39
full name Michael Jordan, and otherwise it would be one or something smaller than one.
8:45
And that's just one row in this matrix.
8:47
You might think of all of the other rows as in parallel asking some other kinds of
8:51
questions, probing at some other sorts of features of the vector being processed.
8:56
Very often this step also involves adding another vector to the output,
8:59
which is full of model parameters learned from data.
9:02
This other vector is known as the bias.
9:05
For our example, I want you to imagine that the value of this
9:08
bias in that very first component is negative one,
9:11
meaning our final output looks like that relevant dot product, but minus one.
9:16
You might very reasonably ask why I would want you to assume that the
9:19
model has learned this, and in a moment you'll see why it's very clean
9:23
and nice if we have a value here which is positive if and only if a vector
9:28
encodes the full name Michael Jordan, and otherwise it's zero or negative.
9:33
The total number of rows in this matrix, which is something
9:36
like the number of questions being asked, in the case of GPT-3,
9:39
whose numbers we've been following, is just under 50,000.
9:43
In fact, it's exactly four times the number of dimensions in this embedding space.
9:46
That's a design choice.
9:47
You could make it more, you could make it less,
9:49
but having a clean multiple tends to be friendly for hardware.
9:52
Since this matrix full of weights maps us into a higher dimensional space,
9:56
I'm gonna give it the shorthand W up.
9:59
I'll continue labeling the vector we're processing as E,
10:02
and let's label this bias vector as B up and put that all back down in the diagram.
10:09
At this point, a problem is that this operation is purely linear,
10:12
but language is a very non-linear process.
10:15
If the entry that we're measuring is high for Michael plus Jordan,
10:19
it would also necessarily be somewhat triggered by Michael plus Phelps
10:23
and also Alexis plus Jordan, despite those being unrelated conceptually.
10:28
What you really want is a simple yes or no for the full name.
10:32
So the next step is to pass this large intermediate
10:35
vector through a very simple non-linear function.
10:38
A common choice is one that takes all of the negative values and
10:41
maps them to zero and leaves all of the positive values unchanged.
10:46
And continuing with the deep learning tradition of overly fancy names,
10:50
this very simple function is often called the rectified linear unit, or ReLU for short.
10:56
Here's what the graph looks like.
10:58
So taking our imagined example where this first entry of the intermediate vector is one,
11:03
if and only if the full name is Michael Jordan and zero or negative otherwise,
11:07
after you pass it through the ReLU, you end up with a very clean value where
11:12
all of the zero and negative values just get clipped to zero.
11:16
So this output would be one for the full name Michael Jordan and zero otherwise.
11:20
In other words, it very directly mimics the behavior of an AND gate.
11:25
Often models will use a slightly modified function that's called the GELU,
11:29
which has the same basic shape, it's just a bit smoother.
11:32
But for our purposes, it's a little bit cleaner if we only think about the ReLU.
11:36
Also, when you hear people refer to the neurons of a transformer,
11:40
they're talking about these values right here.
11:42
Whenever you see that common neural network picture with a layer of dots and a
11:47
bunch of lines connecting to the previous layer, which we had earlier in this series,
11:52
that's typically meant to convey this combination of a linear step,
11:56
a matrix multiplication, followed by some simple term-wise nonlinear function like a ReLU.
12:02
You would say that this neuron is active whenever this value
12:05
is positive and that it's inactive if that value is zero.
12:10
The next step looks very similar to the first one.
12:12
You multiply by a very large matrix and you add on a certain bias term.
12:16
In this case, the number of dimensions in the output is back down to the size of
12:21
that embedding space, so I'm gonna go ahead and call this the down projection matrix.
12:26
And this time, instead of thinking of things row by row,
12:28
it's actually nicer to think of it column by column.
12:31
You see, another way that you can hold matrix multiplication in your head is to
12:36
imagine taking each column of the matrix and multiplying it by the corresponding
12:40
term in the vector that it's processing and adding together all of those rescaled columns.
12:46
The reason it's nicer to think about this way is because here the columns have the same
12:51
dimension as the embedding space, so we can think of them as directions in that space.
12:56
For instance, we will imagine that the model has learned to make that
12:59
first column into this basketball direction that we suppose exists.
13:04
What that would mean is that when the relevant neuron in that first position is active,
13:08
we'll be adding this column to the final result.
13:11
But if that neuron was inactive, if that number was zero, then this would have no effect.
13:16
And it doesn't just have to be basketball.
13:18
The model could also bake into this column and many other features that
13:21
it wants to associate with something that has the full name Michael Jordan.
13:26
And at the same time, all of the other columns in this matrix are telling you
13:31
what will be added to the final result if the corresponding neuron is active.
13:37
And if you have a bias in this case, it's something that you're
13:40
just adding every single time, regardless of the neuron values.
13:44
You might wonder what's that doing.
13:45
As with all parameter-filled objects here, it's kind of hard to say exactly.
13:49
Maybe there's some bookkeeping that the network needs to do,
13:52
but you can feel free to ignore it for now.
13:54
Making our notation a little more compact again,
13:57
I'll call this big matrix W down and similarly call that bias vector B down and
14:02
put that back into our diagram.
14:04
Like I previewed earlier, what you do with this final result is add it to the vector
14:09
that flowed into the block at that position and that gets you this final result.
14:13
So for example, if the vector flowing in encoded both first name Michael and last name
14:19
Jordan, then because this sequence of operations will trigger that AND gate,
14:23
it will add on the basketball direction, so what pops out will encode all of those
14:28
together.
14:29
And remember, this is a process happening to every one of those vectors in parallel.
14:34
In particular, taking the GPT-3 numbers, it means that this block doesn't just
14:39
have 50,000 neurons in it, it has 50,000 times the number of tokens in the input.
14:48
So that is the entire operation, two matrix products,
14:51
each with a bias added and a simple clipping function in between.
14:56
Any of you who watched the earlier videos of the series will recognize this
14:59
structure as the most basic kind of neural network that we studied there.
15:03
In that example, it was trained to recognize handwritten digits.
15:06
Over here, in the context of a transformer for a large language model,
15:10
this is one piece in a larger architecture and any attempt to interpret
15:15
what exactly it's doing is heavily intertwined with the idea of encoding
15:19
information into vectors of a high-dimensional embedding space.
15:24
That is the core lesson, but I do wanna step back and reflect on two different things,
15:28
the first of which is a kind of bookkeeping, and the second of which
15:32
involves a very thought-provoking fact about higher dimensions that
15:35
I actually didn't know until I dug into transformers.
Counting parameters
15:41
In the last two chapters, you and I started counting up the total number of parameters
15:45
in GPT-3 and seeing exactly where they live, so let's quickly finish up the game here.
15:51
I already mentioned how this up projection matrix has just under 50,000 rows and
15:56
that each row matches the size of the embedding space, which for GPT-3 is 12,288.
16:03
Multiplying those together, it gives us 604 million parameters just for that matrix,
16:08
and the down projection has the same number of parameters just with a transposed shape.
16:14
So together, they give about 1.2 billion parameters.
16:18
The bias vector also accounts for a couple more parameters,
16:20
but it's a trivial proportion of the total, so I'm not even gonna show it.
16:24
In GPT-3, this sequence of embedding vectors flows through not one,
16:29
but 96 distinct MLPs, so the total number of parameters devoted
16:34
to all of these blocks adds up to about 116 billion.
16:38
This is around 2 thirds of the total parameters in the network,
16:42
and when you add it to everything that we had before, for the attention blocks,
16:46
the embedding, and the unembedding, you do indeed get that grand total of 175
16:50
billion as advertised.
16:53
It's probably worth mentioning there's another set of parameters associated
16:56
with those normalization steps that this explanation has skipped over,
16:59
but like the bias vector, they account for a very trivial proportion of the total.
Superposition
17:05
As to that second point of reflection, you might be wondering if
17:09
this central toy example we've been spending so much time on
17:12
reflects how facts are actually stored in real large language models.
17:16
It is true that the rows of that first matrix can be thought of as
17:19
directions in this embedding space, and that means the activation of each
17:23
neuron tells you how much a given vector aligns with some specific direction.
17:27
It's also true that the columns of that second matrix tell
17:30
you what will be added to the result if that neuron is active.
17:34
Both of those are just mathematical facts.
17:37
However, the evidence does suggest that individual neurons very rarely
17:41
represent a single clean feature like Michael Jordan,
17:44
and there may actually be a very good reason this is the case,
17:48
related to an idea floating around interpretability researchers these
17:52
days known as superposition.
17:54
This is a hypothesis that might help to explain both why the models are
17:58
especially hard to interpret and also why they scale surprisingly well.
18:03
The basic idea is that if you have an n-dimensional space and you wanna
18:07
represent a bunch of different features using directions that are all
18:11
perpendicular to one another in that space, you know,
18:14
that way if you add a component in one direction,
18:16
it doesn't influence any of the other directions,
18:19
then the maximum number of vectors you can fit is only n, the number of dimensions.
18:24
To a mathematician, actually, this is the definition of dimension.
18:28
But where it gets interesting is if you relax that
18:30
constraint a little bit and you tolerate some noise.
18:34
Say you allow those features to be represented by vectors that aren't exactly
18:38
perpendicular, they're just nearly perpendicular, maybe between 89 and 91 degrees apart.
18:44
If we were in two or three dimensions, this makes no difference.
18:48
That gives you hardly any extra wiggle room to fit more vectors in,
18:51
which makes it all the more counterintuitive that for higher dimensions,
18:55
the answer changes dramatically.
18:57
I can give you a really quick and dirty illustration of this using some
19:01
scrappy Python that's going to create a list of 100-dimensional vectors,
19:06
each one initialized randomly, and this list is going to contain 10,000 distinct vectors,
19:11
so 100 times as many vectors as there are dimensions.
19:15
This plot right here shows the distribution of angles between pairs of these vectors.
19:20
So because they started at random, those angles could be anything from 0 to 180 degrees,
19:25
but you'll notice that already, even just for random vectors,
19:28
there's this heavy bias for things to be closer to 90 degrees.
19:32
Then what I'm going to do is run a certain optimization process that iteratively nudges
19:37
all of these vectors so that they try to become more perpendicular to one another.
19:42
After repeating this many different times, here's
19:44
what the distribution of angles looks like.
19:47
We have to actually zoom in on it here because all of the possible angles
19:51
between pairs of vectors sit inside this narrow range between 89 and 91 degrees.
19:58
In general, a consequence of something known as the Johnson-Lindenstrauss
20:02
lemma is that the number of vectors you can cram into a space that are nearly
20:06
perpendicular like this grows exponentially with the number of dimensions.
20:11
This is very significant for large language models,
20:14
which might benefit from associating independent ideas with nearly
20:18
perpendicular directions.
20:20
It means that it's possible for it to store many,
20:22
many more ideas than there are dimensions in the space that it's allotted.
20:27
This might partially explain why model performance seems to scale so well with size.
20:32
A space that has 10 times as many dimensions can store way,
20:36
way more than 10 times as many independent ideas.
20:40
And this is relevant not just to that embedding space where the vectors
20:43
flowing through the model live, but also to that vector full of neurons
20:47
in the middle of that multilayer perceptron that we just studied.
20:50
That is to say, at the sizes of GPT-3, it might not just be probing at 50,000 features,
20:56
but if it instead leveraged this enormous added capacity by using
20:59
nearly perpendicular directions of the space, it could be probing at many,
21:04
many more features of the vector being processed.
21:07
But if it was doing that, what it means is that individual
21:10
features aren't gonna be visible as a single neuron lighting up.
21:14
It would have to look like some specific combination of neurons instead, a superposition.
21:20
For any of you curious to learn more, a key relevant search term here is sparse
21:24
autoencoder, which is a tool that some of the interpretability people use to try to
21:28
extract what the true features are, even if they're very superimposed on all these
21:32
neurons.
21:33
I'll link to a couple really great anthropic posts all about this.
Up next
21:37
At this point, we haven't touched every detail of a transformer,
21:40
but you and I have hit the most important points.
21:43
The main thing that I wanna cover in a next chapter is the training process.
21:48
On the one hand, the short answer for how training works is that it's all
21:51
backpropagation, and we covered backpropagation in a separate context with earlier
21:55
chapters in the series.
21:57
But there is more to discuss, like the specific cost function used for language models,
22:02
the idea of fine-tuning using reinforcement learning with human feedback,
22:06
and the notion of scaling laws.
22:08
Quick note for the active followers among you,
22:11
there are a number of non-machine learning-related videos that I'm excited to
22:14
sink my teeth into before I make that next chapter, so it might be a while,
22:18
but I do promise it'll come in due time.
22:35
Thank you.

----

But how do AI images and videos actually work? | Guest video by Welch Labs

Sections
0:00 - Intro
3:37 - CLIP
6:25 - Shared Embedding Space
8:16 - Diffusion Models & DDPM
11:44 - Learning Vector Fields
22:00 - DDIM
25:25 - Dall E 2
26:37 - Conditioning
30:02 - Guidance
33:39 - Negative Prompts
34:27 - Outro
35:32 - About guest videos


Intro
0:03
Over the last few years, AI systems have become astonishingly good at turning text props into videos.
0:10
At the core of how these models operate is a deep connection to physics. This generation of image and video models works using a process known as diffusion,
0:19
which is remarkably equivalent to the Brownian motion we see as particles diffuse, but with time run backwards, and in high-dimensional space.
0:28
As we'll see, this connection to physics is much more than a curiosity. We get real algorithms out of the physics that we can use to generate images and videos.
0:36
And this perspective will also give us some really nice intuitions for how these models work in practice.
0:42
But before we dive into this connection, let's get hands-on with a real diffusion model.
0:47
While the best models are closed source, there are some compelling open source models.
0:52
This video of an astronaut was generated by an open source model called WAN 2.1. We can add to our prompt and have our astronaut hold a flag,
1:01
hold a laptop, or hold a meeting. If we cut down our prompt to just an astronaut, we get this.
1:08
And if we cut down our prompt to nothing, we interestingly still get this video of a woman.
1:13
If we dig into our WAN model's source code, we'll find that the video generation process begins with this call to a random number generator.
1:21
Creating a video where the pixel intensity values are chosen randomly. Here's what it looks like.
1:27
From here, this pure noise video is passed into a transformer. This is the same type of AI model used by large language models, like ChatGPT.
1:36
But instead of outputting text, this transformer outputs another video that now looks like this.
1:42
Still mostly noise, but with some hints of structure. This new video is added to our pure noise video,
1:48
and then passed back into the model again, producing a third video that looks like this.
1:54
This process is repeated again and again. Here's what the video looks like after 5 iterations, 10, 20, 30, 40, and finally 50.
2:05
Step by step, our transformer shapes pure noise into incredibly realistic video.
2:11
But what exactly is the connection to Brownian motion here? And how is our model able to use text input so expressively
2:19
to shape noise into what our prompt describes? In this video, we'll impact diffusion models in 3 parts.
2:26
First we'll look at a 2021 OpenAI paper and model called CLIP. As we'll see, CLIP is really two models, a language model and a vision model,
2:34
that are trained using a clever learning objective that allows them to learn this really powerful shared space between words and pictures.
2:43
Experimenting with this space will help us get a feel for the high dimensional spaces that diffusion models operate in.
2:50
But learning a shared representation is not enough to generate images. From here we'll look at the diffusion process itself.
2:56
At a high level, diffusion models are trained to remove noise from images or videos.
3:02
However, if you dig into the landmark papers in the field, you'll find that this naive understanding of diffusion really doesn't hold
3:08
up in practice. In this section we'll dig into the connection between diffusion models and diffusion processes in physics.
3:15
This connection will help us understand how these models really work in practice and give us some powerful theory for dramatically speeding up image and video generation.
3:25
Finally, we'll bring these worlds together and see how approaches like CLIP are combined with diffusion models to condition and guide
3:31
the generation process towards the videos we ask for in our prompts.
CLIP
3:37
2020 was a landmark year for language modeling. New results in neural scaling laws and OpenAI's
3:43
GPT-3 showed that bigger really was better. Massive models trained on massive datasets had
3:50
capabilities that simply didn't exist in smaller models. It didn't take long for researchers to apply similar ideas to images.
3:58
In February 2021, a team at OpenAI released a new model architecture called CLIP, trained on a dataset of 400 million image and caption pairs scraped from the internet.
4:08
CLIP is composed of two models, one that processes text and one that processes images.
4:14
The output of each of these models is a vector of length 512, and the central idea is that the vectors for a given image and its captions
4:21
should be similar. To achieve this, the OpenAI team developed a clever training approach.
4:28
Given a batch of image-caption pairs, for example our batch could contain a picture of a cat, a dog, and me, with the captions a photo of a cat,
4:36
a photo of a dog, and a photo of a man, we then pass our three images into our image model, and our three captions into our text model.
4:44
We now have three image vectors and three text vectors, and we would like the vectors for the matching image-caption pairs to be similar.
4:52
The clever idea from here is to make use of the similarity not just between the corresponding images and captions,
4:57
but between all image-caption pairs in the batch when training our models. If we arrange our image vectors as the columns of a matrix,
5:04
and our text vectors as the rows, the pairs of vectors along the diagonal of our matrix correspond to matching images and captions.
5:11
And all the pairs off-diagonal are non-matching images and captions. The CLIP training objective seeks to maximize the similarity between
5:19
corresponding image-caption pairs, while simultaneously minimizing the similarity between non-corresponding image-caption pairs.
5:28
The C in CLIP stands for contrastive, because the model learns to contrast matching and non-matching image-caption pairs.
5:36
The CLIP algorithm measures similarity between vectors using a metric called cosine similarity.
5:41
Geometrically, we can think of each of these vectors as pointing in some direction in high-dimensional space.
5:47
Cosine similarity measures the cosine of the angle between our vectors in this space.
5:53
So if our text and image vector point in the same direction, the angle between our vectors will be zero, resulting in a maximum value for our cosine
6:00
similarity score of 1. So the image and text models that make up CLIP are trained to maximize the
6:07
alignment of related images and captions in this shared high-dimensional space, while minimizing the alignment between unrelated images and captions.
6:16
The learned geometry of this shared vector space, known as a latent or embedding space, has some really interesting properties.
6:24
If I take two pictures of myself, one not wearing a hat and one wearing a hat, and pass both of these into our CLIP image model,
Shared Embedding Space
6:31
we get two vectors in our embedding space. Now if I take the vector corresponding to me wearing a hat,
6:38
and subtract the vector of me not wearing a hat, we get a new vector in our embedding space.
6:43
Now what text might this new vector correspond to? Mathematically we took the difference of me wearing a hat and me not wearing a hat.
6:52
We can search for corresponding text by passing a bunch of different words into our text encoder, and for each computing the cosine similarity
6:59
between our newly computed difference vector and the text vector. Testing a set of a few hundred common words, the top ranked match with
7:08
a similarity of 0.165 is the word hat, followed by cap and helmet.
7:13
This is a remarkable result. The learned geometry of CLIP's embedding space allows us to operate
7:20
mathematically on the pure ideas or concepts in our images and text, translating the differences in the content of our images,
7:27
like if there's a hat or not, into a literal distance between vectors in our embedding space.
7:33
The OpenAI team showed that CLIP could produce very impressive image classification results by simply passing an image into our image encoder,
7:41
and then comparing the resulting vector to a set of possible captions, one for each label that could be assigned to the image,
7:48
and classifying the image with whatever label resulted in the highest cosine similarity.
7:54
So techniques like CLIP give us a powerful shared representation of image and text, a kind of vector space of pure ideas.
8:02
However, our CLIP models only go one direction. We can only map image and text to our shared embedding space.
8:10
We have no way of generating images and text from our embedding vectors.
8:15
2020 turned out not only to be a transformative year for language modeling. A few weeks after the GPT-3 paper came out, a team at Berkeley published a
Diffusion Models & DDPM
8:25
paper called Denoising Diffusion Probabilistic Models, now known as DDPM.
8:30
The paper showed for the first time that it was possible to generate very high quality images using a diffusion process,
8:37
where pure noise is transformed step by step into realistic images.
8:42
The core idea behind diffusion models is pretty straightforward. We take a set of training images and add noise to each
8:49
image step by step until the image is completely destroyed. From here we train a neural network to reverse this process.
8:57
When I first learned about diffusion models, I assumed that the models would be trained to remove noise a single step at a time.
9:04
Our model would be trained to predict the image in step 1 given the noisier image in step 2, trained to predict the image in step 2 given the noisier image in step 3, and so on.
9:14
When it came time to generate an image, we would pass pure noise into our model, take its output and pass it back into its input again and again,
9:22
and after enough steps we would have a nice image. Now, it turns out that this naive approach to
9:28
building a diffusion model really does not work well. Virtually no modern models work like this.
9:35
These are the training and image generation algorithms from the Berkeley team's paper. The notation is a bit dense, but there's some key details we can pull out
9:43
that will help us understand what it takes to make these models really work. The first thing that surprised me is that the team added random noise
9:51
to images not just during training, but also during image generation. Algorithm 2 tells us that when generating new images, at each step,
9:59
after our neural network predicts a less noisy image, we need to add random noise to this image before passing it back into our model.
10:08
This added noise turns out to matter a lot in practice. If we take a popular diffusion model like stable diffusion 2 and use the Berkeley team's
10:17
image generation approach, known as DDPM sampling, we can get some really nice images.
10:23
Here's the image we get when prompting the model with this prompt, asking for a tree in the desert.
10:28
Now, if we remove the line of code that adds noise at each step of the generation process, we end up with a tiny sad blurry tree.
10:37
How is it that adding random noise while generating images leads to better quality, sharper images?
10:43
The second thing that surprised me when I encountered the Berkeley team's approach was that the team wasn't training models to reverse a single step in the noise addition
10:51
process. Instead, the team takes an initial clean image, which they call X0, and adds scaled random noise to the image, which they call epsilon.
11:00
And from here, they train the model to predict the total noise that was added to the original image.
11:06
So the team is effectively asking the model to skip all the intermediate steps and make a prediction about the original image.
11:14
Intuitively, this learning task seems much more difficult to me than just learning to make a noisy image slightly less noisy.
11:21
The Berkeley team's paper and approach was a landmark result that put diffusion on the map.
11:26
Why does adding random noise while generating images and training the model like this work so well?
11:33
The DDPM paper draws on some fairly complex theory to arrive at these algorithms.
11:38
I'll include a link to a great tutorial in the description if you want to dig deeper into the theory.
11:43
Happily, it turns out that there's a different but mathematically equivalent way of understanding what diffusion models are really learning that we can
Learning Vector Fields
11:50
use to get a visual and intuitive sense for why the DDPM algorithms work so well. The key will be thinking of diffusion models as learning a time-varying vector field.
12:00
This perspective also leads to a more general approach called flow-based models, which have become very popular recently.
12:07
To see how diffusion models learn this time-varying vector field, let's temporarily simplify our learning problem.
12:14
One way to think about an image is as a point in high-dimensional space, where the intensity value of each pixel controls the position of the point in each
12:22
dimension. If we reduce the size of our images to only two pixels, we can visualize the distribution of our images by plotting the pixel intensity
12:31
value of our first pixel on the x-axis of scatterplot and the pixel intensity of our second pixel on the y-axis.
12:38
So an image with a black first pixel and a white second pixel would show up at x equals zero and y equals one on our scatterplot.
12:45
And an all-white image would be at one, one, and so on. Now, real images have a very specific structure in this high-dimensional space.
12:53
Let's create some structure for our points in our lower two-dimensional space for our diffusion model to learn.
12:59
The exact structure we choose doesn't matter too much at this point. Let's start with a spiral shape like this.
13:05
The core idea of diffusion models, adding more and more noise to an image and then training a neural network to reverse this process,
13:12
looks really interesting from the perspective of our 2D toy data. When we add random noise to an image, we're effectively
13:20
changing each pixel's value by a random amount. In our toy 2D dataset, where the coordinates of a point correspond
13:27
to that image's pixel intensity values, adding random noise is equivalent to taking a step in a randomly chosen direction.
13:34
As we add more and more noise to our image, our point goes on a random walk. This process is equivalent to the Brownian motion that drives diffusion
13:42
processes in physics and is where diffusion models get their name. From here, it's pretty wild to think about what we're asking our diffusion model to do.
13:51
Our model will see many different random walks from various starting points in our dataset, and we're effectively asking our model to reverse the clock,
13:59
removing noise from our images by letting it play these diffusion processes backwards, starting our points from random locations and recovering the original structure of
14:08
our dataset. How can our model learn to reverse these random walks?
14:14
If we consider the specific point at the end of this 100-step random walk, in our naive diffusion modeling approach, where we ask our model to denoise images a
14:23
single step at a time, this is equivalent to giving our model the coordinates of the final 100th point in our walk, and asking our model to predict the coordinates of our
14:32
point at the 99th step. Although the direction of our 100th step is chosen randomly,
14:38
there will be some signal in aggregate for our model to learn from here. Given enough training points, we expect many diffusion paths to go through
14:46
this neighborhood, and on average our points will be diffusing away from our starting spiral, so our model can learn to point back towards our spiral.
14:56
We can now see why the Berkeley team's training objective works so well. Instead of training the model to remove noise from images one step at a time,
15:05
this would correspond to predicting the coordinates of the 99th step given the 100th, the team instead trained the model to predict the total noise added across the entire
15:13
walk. On our plot, this is the vector pointing from our 100th step back to the original starting point of the walk.
15:20
It turns out that we can prove that learning to predict the noise added in the final step of our walk is mathematically equivalent to learning
15:27
to predict the total noise added, divided by the number of steps taken. This means that when our model learns to reverse a single step,
15:35
although our training data is noisy, we expect our model to ultimately learn to point back towards x0.
15:42
By instead training our model to directly predict the vector pointing back towards x0, we're significantly reducing the variance of our training examples,
15:51
allowing our model to learn much more efficiently, without actually changing our underlying learning objective.
15:58
So for each point in our space, our model learns the direction pointing back towards the original data distribution.
16:05
This is also known as a score function, and the intuition here is that the score function points us towards more likely, less noisy data.
16:14
Now, in practice, these learned directions depend heavily on how much noise we add to our original data.
16:20
After 100 steps, most of our points are far from their starting points, so our model learns to move these points back in the general direction of our spiral.
16:29
However, if we train our model on examples after only one diffusion step, we end up with a much more nuanced vector field,
16:36
pointing to the fine structure of our spiral. There turns out to be a clever solution to this problem.
16:42
Instead of just passing in the coordinates of our point into our model, which we'll write here as a function f, we can also pass in a time
16:50
variable that corresponds to the number of steps taken in our random walk. If we set t equal to 1 at our 100th step, then t would equal 0.99 at our 99th step,
17:00
and so on. Conditioning our models on time like this turns out to be essential in practice,
17:06
allowing our model to learn coarse vector fields for large values of t, and very refined structures as t approaches 0.
17:13
After training, we can watch the time evolution of our model. We see this really interesting behavior as t approaches 0.4.
17:23
Our learned vector field suddenly transitions, from pointing towards the center of the spiral to pointing towards the spiral itself.
17:29
It feels like a phase change. We're now in a great position to resolve the final mystery of the DDPM paper.
17:38
How is it that adding random noise at each step while generating images leads to better quality, sharper images?
17:45
Let's follow the path of a single point guided by the DDPM image generation algorithm.
17:51
On our 2D dataset, generating an image is equivalent to starting at a random location and working our way back to our spiral.
17:59
Starting at a randomly chosen location of x equals minus 1.6 and y equals 1.8, our model's vector field points us back towards our spiral.
18:08
Following the DDPM algorithm, we take a small step in the direction returned by our model, and add scaled random noise, which effectively moves our point in a random
18:17
direction. We'll color the steps driven by our diffusion model in blue, and our random steps in gray.
18:24
Note that the scale of the random step may seem large, but following our DDPM algorithm, the size of our random steps will come down as we progress.
18:33
Repeating this process for 64 steps, our particle jumps around quite a bit due to both our learned vector field changing and our random noise steps,
18:42
but ultimately lands nicely on our spiral. Repeating this process for a point cloud of 256 points,
18:49
our reverse diffusion process starts out looking like absolute chaos, but does converge nicely, with most points landing on our spiral.
18:58
Now, what happens if we remove the noise addition steps? Running our reverse diffusion process again without the random noise step,
19:07
all of our points quickly move to the center of our spiral, and then make their way towards a single inside edge of the spiral.
19:14
This result can help us make sense of why we saw a sad blurry tree earlier when we removed this random noise step.
19:21
Instead of capturing our full spiral distribution, as we did when we included a noise step, all of our generated points end up close to
19:28
the center or average of our spiral. In the space of images, averages look blurry.
19:36
Conceptually, we can imagine different parts of our spiral corresponding to different images of trees in the desert.
19:42
And when we remove the random noise steps from our generation process, our generated images end up in the center or average of these images,
19:49
which looks like a blurry mess. Now, note that the analogy between our toy dataset and
19:55
high dimensional image dataset breaks down a bit here. If all the points on our spiral correspond to realistic images,
20:02
since our generated points do still end up landing on our 2D spiral, we would expect these generated points to still look like real images,
20:09
but likely with less diversity than we would want. However, in the high dimensional space of images,
20:16
it appears that our image generation process doesn't quite make it to the manifold of realistic images, resulting in a blurry non-realistic image.
20:25
This prediction of the average is not a coincidence. It turns out that we can show mathematically that our model
20:31
learns to point to the mean or average of our dataset, conditioned on our input point and the time in our diffusion process.
20:39
One way to arrive at this result is to show that given the noise we add in our forward process is Gaussian, for sufficiently small step sizes our reverse process will also
20:48
follow a Gaussian distribution, where our model actually learns the mean of this distribution.
20:54
Since our model just predicts the mean of our normal distribution, to actually sample from this distribution, we need to add zero mean
21:02
Gaussian noise to our model's predicted value, which is precisely what the DDPM image generation process does when we
21:08
add random noise after each step. We can see this mean learning behavior most clearly early in our reverse diffusion
21:16
process, when t is close to 1 and our training points are far from our spiral. Our model's learned vector field points towards the center or average of our dataset.
21:26
So adding random noise during image generation falls nicely out of theory, and in practice prevents all our points from landing near the center or average of
21:33
our dataset. The DDPM paper put diffusion models on the map as a viable method of generating images,
21:40
but the diffusion approach did not immediately see widespread adoption. A key issue with the DDPM approach at the time was the high compute demands of
21:49
the large number of steps required to generate high quality images, since each step required a complete pass through a potentially very large neural network.
21:58
A few months later, a pair of papers from teams at Stanford and Google showed that it's remarkably possible to generate high quality images without actually adding random
DDIM
22:07
noise during the generation process, significantly reducing the number of steps required.
22:13
The DDPM image generation process we've been looking at can be expressed using a special type of differential equation known as a stochastic differential equation.
22:22
This first term represents the motion of our point driven by our model's vector field, and the second term represents the random motions of our point.
22:30
Adding these terms together, we get the overall motion of our point at each step, dx.
22:35
From here, we can consider how the distribution of all of our points evolves over time, where the motion of each point is governed by this stochastic differential equation.
22:45
This problem has been well studied in physics. Using a key result from statistical mechanics known as the Fokker-Planck equation,
22:52
the Google Brain team showed that there's another differential equation, this time an ordinary differential equation with no random component,
23:00
that results in the same exact final distribution of points as our stochastic differential equation.
23:07
This result gives us a new algorithm for generating images using our model's learned vector fields that does not require taking random steps along the way.
23:17
Exactly how our ordinary differential equation maps to an image generation algorithm is a bit technical.
23:23
I'll leave a link to a tutorial in the description. The key result here though, is that we end up with something that looks very
23:30
similar to our DDPM image generation process, but without the random noise addition at each step,
23:35
and with a new scaling for the sizes of steps that we take. This approach is generally known as DDIM.
23:43
The scaling of our step sizes, and especially how these step sizes vary throughout a reverse diffusion process, matters a lot in practice.
23:52
When we just removed the random noise steps from our DDPM generation algorithm earlier, all of our points ended up near the mean of our data,
24:00
and we saw blurry results for our generated images. Switching to our DDIM approach, we now have smaller scaling for our step
24:08
sizes that allow our trajectories to better follow the contour lines of our vector field, and land nicely on the correct spiral distribution.
24:18
And applying our DDIM algorithm to our tree in the desert example, we're now able to generate nice results.
24:24
Comparing to our original DDPM algorithm that required random steps, DDIM remarkably does not require any changes to model training,
24:33
but is able to generate high quality images in significantly fewer steps, completely deterministically.
24:40
Note that the theory does not tell us that our individual images or points on our spiral will be the same, but instead that our final
24:47
distribution of points or images will be the same, regardless of whether we use our stochastic DDPM algorithm or our
24:54
deterministic DDIM algorithm. The WAN model we saw earlier uses a generalization of DDIM called flow matching.
25:03
By early 2021, it was clear that diffusion models were capable of generating high quality images, and thanks to image generation methods like DDIM,
25:11
it was possible to generate these images without using enormous amounts of compute.
25:17
However, our ability to steer the diffusion process using text prompts was still very limited.
25:23
Earlier, we saw how CLIP was able to learn a powerful shared representation of images and text by concurrently training image and text encoder models.
Dall E 2
25:32
However, these models only go one way, converting text or images into embedding vectors.
25:38
These two problems potentially fit together in a really interesting way. Diffusion models are able to potentially reverse the CLIP image encoder,
25:47
generating high quality images, and the output vector of the CLIP text encoder could be used to guide our diffusion models toward the images or videos that we want.
25:57
So the high level idea here is that we could pass in a prompt into the CLIP text encoder to generate an embedding vector, and use this embedding vector to steer
26:06
the diffusion process towards the image or video of what our prompt describes.
26:11
A team at OpenAI did exactly this in 2022. Using image and caption pairs to train a diffusion model to invert the CLIP image encoder.
26:21
Their approach yielded an incredible level of prompt adherence, capturing an unprecedented level of detail from the input text.
26:29
The team called their method unCLIP, but their model is better known by its commercial name, DALI2.
26:35
But how do we actually use the embedding vectors for models like CLIP to steer the diffusion process?
Conditioning
26:41
One option is to simply pass our text vector as another input into our diffusion model, and train as we normally would to remove noise.
26:49
If we train our diffusion model using image and caption pairs, as the OpenAI team did, the idea here is that the model will learn to
26:56
use the text information to more accurately remove noise from images, since it now has more context about the image that it's learning to denoise.
27:05
This technique is called conditioning. We used a similar approach earlier, when we conditioned our toy diffusion
27:11
model on the number of time steps elapsed in the diffusion process, allowing the model to learn coarse structure for large values of t,
27:18
and finer structures as our training samples get closer to our original spiral.
27:23
Interestingly, there turns out to be a variety of ways we can pass in the text vector into our diffusion model.
27:30
Some approaches use a mechanism called cross-attention to couple image and text information.
27:35
Other approaches simply add or append the embedded text vector to our diffusion model's input, and some approaches pass in text information in multiple ways at once.
27:45
Now it turns out that conditioning alone is not enough to achieve the level of prompt adherence that we see in models like DALI2.
27:53
If we take the stable diffusion tree in the desert example we've been experimenting with, and only condition our model with our text inputs,
28:01
the model no longer gives us everything we ask for. We get a shadow in a desert, but no tree.
28:08
Note that stable diffusion was developed by a team at Heidelberg University around the same time as DALI2, and works in a similar way, but is open source.
28:17
It turns out that there's one more powerful idea that we need to effectively steer our diffusion models.
28:23
We can see this idea in action by returning to our toy dataset one last time. If our overall spiral corresponds to realistic images,
28:30
then different sections of our spiral may correspond to different types of images. Let's say this inner part is images of people, this middle part is images of dogs,
28:40
and this outer part is different images of cats. Now let's train the same diffusion model we trained earlier,
28:46
but in addition to passing in our starting coordinates and the time of our diffusion process, we'll also pass in the points class.
28:53
Person, cat, or dog. This extra signal should allow our model to steer points to the right sections of our spiral, based on each points class.
29:03
Running our generation process, after assigning person, dog, or cat labels to each point, we see that we're able to recover the overall structure of our dataset,
29:11
but the fit is not great, and we see some confusion here between people and dog images.
29:18
Part of the problem here is that we're asking our model to simultaneously learn to point to our overall spiral of realistic images, and toward specific classes on our spiral.
29:28
If we consider this cat point for example, it starts off heading towards the center of our spiral, and as our class conditioned vector
29:35
field shifts to point towards a cat region of our spiral, our point moves towards this part of the spiral, but it doesn't quite make it.
29:44
The modeling task of generally matching our overall spiral has overpowered our model's ability to move our point in the direction of a specific class.
29:53
Now, is there a way to decouple and maybe even control these two factors? Remarkably, it turns out that we can.
30:00
The trick is to leverage the differences between the unconditional model that is not trained on a specific class, and a model that is conditioned on specific classes.
Guidance
30:09
We could do this by training two separate models, but in practice it's more efficient to just leave out the class information for a
30:15
subset of our training examples. We now have the option of effectively passing in no class or text
30:21
information into our model, and getting back a vector field that points towards our data in general, not towards any specific class.
30:29
We can visualize these two vector fields together. Here the gray vectors show our diffusion model points when we don't pass in any class
30:36
information, and these yellow vectors show when our model is conditioned on the cat class.
30:42
For large values of our diffusion time variable when our training data is far from our spiral, our two vector fields basically point
30:48
in the same direction, roughly towards the average of our spiral. But as time approaches zero, our vector fields diverge,
30:56
with our cat conditioned vector field pointing more towards the outer cat portion of our spiral.
31:02
Now that we have these two separate directions, we can use their differences to push our points more in the direction
31:08
of the class we want. Specifically, we take our yellow class conditioned
31:13
vector and subtract our gray unconditioned vector. This gives us a new vector pointing from the tip of our
31:18
unconditioned vector to the tip of our conditioned vector. The idea from here is that this direction should point more in the direction of our
31:26
cat examples, now that we've removed the direction generally pointing towards our data.
31:31
We can now amplify this direction by multiplying by a scaling factor, alpha, and replace our original conditioned yellow vector with a vector pointing in this new
31:40
direction. Let's follow the trajectory of the same cat point we saw earlier that didn't quite make it onto our spiral.
31:47
We'll roll back our diffusion time variable and start a new green point from the same starting location.
31:53
If we use our new green vectors to guide the diffusion process instead of our original yellow vectors, the difference between our gray arrows that point towards the center
32:02
of our spiral and yellow vectors that start pointing us back towards our cat part of the spiral are amplified, now guiding our point to land nicely on our spiral.
32:11
This approach is called classifier-free guidance. Using our new green vectors to guide a set of cat points,
32:18
we see a nice tight fit to our spiral for this class. Switching to our dog class, our unconditional gray vector field stays the same,
32:26
but our dog conditioned model outputs, shown in magenta, now point us more towards the dog part of our spiral.
32:33
And adding guidance amplifies this learned direction. Using our guided vectors and running our generation process,
32:41
we see a nice fit for our dog points. Finally, we get a third vector field for our people examples
32:47
that again results in nice convergence to our spiral. Classifier-free guidance works remarkably well and has become an
32:55
essential part of many modern image and video generation models. Earlier, we saw that if we only conditioned our stable diffusion model,
33:03
our image would have a desert and a shadow, but no tree that we asked for in the prompt.
33:08
If we add classifier-free guidance to this model, once we reach a guidance scale alpha of around 2,
33:14
we start to actually see a tiny tree in our images. And the size and detail of our tree improve as we increase our scaling factor, alpha.
33:23
The fact that this works so well is remarkable to me. As we use guidance to point our stable diffusion model's vector field more in the
33:31
direction of our prompt, our tree literally grows in size and detail in our images.
33:37
Our WAN video generation model takes this guidance approach one step further. Instead of subtracting the output of an unconditioned model with no text input,
Negative Prompts
33:45
the WAN team uses what's known as a negative prompt, where they specifically write out all the features they don't want in their video,
33:52
and then subtract the resulting vector from the model's conditioned output and amplify the result, steering the diffusion process away from these unwanted features.
34:02
Their standard negative prompt is fascinating, including features like extra fingers and walking backwards,
34:08
and interestingly is actually passed into their text encoder in Chinese. Here's a video generated using the same astronaut on a horse prompt we used earlier,
34:17
but without the negative prompt. It's really interesting to see how the parts of the scene get cartoonish and no longer fit together.
34:26
Since the publication of the DDPM paper in the summer of 2020, the field has progressed at a blistering pace,
Outro
34:32
leading to the incredible text-to-video models that we see today.
34:38
Of all the interesting details that make these models tick, the most astounding thing to me is that the pieces fit together at all.
34:46
The fact that we can take a trained text encoder from clip or elsewhere and use its output to actually steer the diffusion process,
34:53
which itself is highly complex, seems almost too good to be true.
34:59
And on top of that, many of these core ideas can be built from relatively simple geometric intuitions that somehow hold in
35:06
the incredibly high dimensional spaces these models operate in. The resulting models feel like a fundamentally new class of machine.
35:15
To create incredibly lifelike and beautiful images and video, you no longer need a camera, you don't need to know how to draw or how to paint,
35:23
or how to use animation software. All you need is language.
35:29
So this, as you can no doubt tell, was a guest video. It comes from Stephen Welsh, who runs the channel WelshLabs.
About guest videos
35:35
If somehow you watch this channel and you're not already familiar with WelshLabs, you should absolutely go and just watch everything that he's made.
35:42
A while back he made this completely iconic series about imaginary numbers. He actually has since turned it into a book, and consistent with everything he makes,
35:50
it's just super high quality, lots of exercises, good stuff like that. More recently he's been doing a lot of machine learning content,
35:56
so cannot recommend his stuff highly enough. Now the context on why I'm doing guest videos at all is that very
36:02
recently my wife and I had our first baby, which I'm very excited about. And I'm not sure what most solo YouTubers do for paternity leave,
36:09
but the way I decided to go about it was to reach out to a few creators whose work I really enjoy, and who I'm quite sure you're going to enjoy, and essentially ask, hey,
36:17
what do you feel about me pointing some of the Patreon funds that come towards this channel towards you during this time that I'm away,
36:24
and kind of commission pieces to fill the airtime while I'm away. The pieces are actually going to be really great.
36:30
I've enjoyed giving some editorial oversight as they're coming in. You know, we've got statistical mechanics, we've got machine learning,
36:36
even some modern art. It's going to be a good time. The next guest video is going to be about a combination of modern art and group theory.
36:43
It's actually very fun. And like all the other videos on this channel, if you're a Patreon supporter, you can get early views of these ones and provide some feedback before they go live.
36:51
Until then, I hope you thoroughly enjoy binge-watching WelshLabs, and again, consider buying the things that he makes.
36:56
There is just as much thought and care put into those as there is into the videos.
37:18
Bye!