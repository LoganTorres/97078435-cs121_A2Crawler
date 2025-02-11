'''

DELETE LATER - just to see what hamming distance looks like

'''
import re
import hashlib
def get_fingerprint(text): # SimHash
    """
    Create a finger print for the given response 'resp'

    @Parameters:
    resp - The response from the cache server which is used to create the fingerprint for near duplication detection

    @Returns:
    Returns a fingerprint which is used for determining near duplication with other fingerprints in self._fingerprints
    """

    webContent = text

    # Get all the tokens on a page (to track length)
    tokens = [token for token in tokenize(webContent)] 

    # Initialize the vector to represent the fingerprint (128 bits)
    vector = [0] * 128

    for token in tokens:

        # Get the hash value for each token
        token_hash = hashlib.md5(token.encode('utf-8')).hexdigest()
        # Convert hash to binary (this will be a string of 128 characters '0' or '1')
        hash_bits = bin(int(token_hash, 16))[2:].zfill(128)

        # Update the vector based on the hash bits
        for i, bit in enumerate(hash_bits):
            # If the bit is '1', increment the corresponding dimension of the vector, else decrement it
            if bit == '1':
                vector[i] += 1
            else:
                vector[i] -= 1

    # Create the final SimHash by converting the vector into a binary string
    simhash = ''.join(['1' if x > 0 else '0' for x in vector])

    # Convert the binary string into a hexadecimal string (the final fingerprint)
    fingerprint = format(int(simhash, 2), '032x')

    return fingerprint

def tokenize(text: str) -> list[str]: # can replace with someone else's
    '''
    Reads a text file and returns a list of alphanumeric tokens in that file.

    Runtime Complexity:
    O(n) where n is the number of characters in a file.
    '''
    tokens = []
    try:
        # Convert the text to lowercase and get a list of alphanumeric tokens using regex
        line_tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
        # Add the new tokens to the tokens list
        tokens.extend(line_tokens)
    except Exception as e:
        print(f"Error while processing text: {e}.")

    return tokens

text1 = """
In the vast and ever-expanding digital landscape, information flows like an endless river, carrying with it the collective knowledge, stories, and innovations of humanity. Every day, billions of people interact with technology in ways that would have been unimaginable just a few decades ago. From the moment we wake up, we are surrounded by digital assistants, smart devices, and a constant stream of notifications that keep us connected to the world. The rapid evolution of artificial intelligence, machine learning, and cloud computing has fundamentally altered the way we work, communicate, and entertain ourselves.

Consider the sheer volume of data generated every second. Every click, every search, every online purchase contributes to a vast ocean of information that organizations harness to improve user experiences, drive business decisions, and enhance the efficiency of countless systems. The rise of big data analytics has made it possible to predict consumer behavior, optimize supply chains, and even anticipate global trends before they become mainstream. But with this abundance of information comes a responsibility to manage it ethically, ensuring that privacy is respected and that technology serves humanity rather than exploits it.

Meanwhile, social media platforms have transformed the nature of human interaction. In the past, communication was largely confined to in-person meetings, letters, and phone calls. Now, a single post can reach millions of people across the globe within seconds. This connectivity has created unprecedented opportunities for collaboration, education, and activism, enabling individuals to share ideas, challenge injustices, and build communities around shared interests. However, it has also introduced new challenges, such as misinformation, online harassment, and the erosion of critical thinking in the face of algorithm-driven content.

As technology continues to advance, the lines between the physical and digital worlds blur. The emergence of virtual reality (VR) and augmented reality (AR) has created immersive experiences that transport users to entirely new dimensions, reshaping industries such as gaming, education, and healthcare. In medicine, AI-powered diagnostic tools assist doctors in detecting diseases earlier and more accurately, improving patient outcomes and reducing the burden on healthcare systems. Autonomous vehicles, once a futuristic concept, are becoming a reality, promising to revolutionize transportation and reduce traffic fatalities.

Yet, with all these advancements, there remains an underlying question: What does it mean to be human in an increasingly digital world? As machines become more capable, creative, and intelligent, society must grapple with ethical dilemmas regarding automation, job displacement, and the role of AI in decision-making. The balance between technological progress and human values must be carefully maintained to ensure that innovation benefits all of humanity rather than a select few.

Looking ahead, the future of technology holds both promise and uncertainty. The continued development of quantum computing could unlock new frontiers in problem-solving, while breakthroughs in biotechnology might extend human lifespans and eradicate diseases. Space exploration, once the domain of government agencies, is now being pursued by private companies, raising the possibility of colonization beyond Earth. The next decades will be defined by our ability to navigate these rapid changes, making choices that prioritize sustainability, equity, and the well-being of future generations.

In the end, technology is merely a tool—one that reflects the intentions of those who create and wield it. Whether it leads to a brighter, more interconnected world or a dystopian future where privacy and autonomy are relics of the past depends on the actions we take today. As individuals, organizations, and societies, we must remain vigilant, thoughtful, and forward-thinking, ensuring that the digital revolution remains a force for good in an ever-changing world.
"""

text2 = """
In the vast and ever-expanding digital landscape, information flows like an endless river, carrying with it the collective knowledge, stories, and innovations of humanity. Every day, billions of people interact with technology in ways that would have been unimaginable just a few decades ago. From the moment we wake up, we are surrounded by digital assistants, smart devices, and a constant stream of notifications that keep us connected to the world. The rapid evolution of artificial intelligence, machine learning, and cloud computing has fundamentally altered the way we work, communicate, and entertain ourselves.

Consider the sheer volume of data generated every second. Every click, every search, every online purchase contributes to a vast ocean of information that organizations harness to improve user experiences, drive business decisions, and enhance the efficiency of countless systems. The rise of big data analytics has made it possible to predict consumer behavior, optimize supply chains, and even anticipate global trends before they become mainstream. But with this abundance of information comes a responsibility to manage it ethically, ensuring that privacy is respected and that technology serves humanity rather than exploits it.

Meanwhile, social media platforms have transformed the nature of human interaction. In the past, communication was largely confined to in-person meetings, letters, and phone calls. Now, a single post can reach millions of people across the globe within seconds. This connectivity has created unprecedented opportunities for collaboration, education, and activism, enabling individuals to share ideas, challenge injustices, and build communities around shared interests. However, it has also introduced new challenges, such as misinformation, online harassment, and the erosion of critical thinking in the face of algorithm-driven content.

As technology continues to advance, the lines between the physical and digital worlds blur. The emergence of virtual reality (VR) and augmented reality (AR) has created immersive experiences that transport users to entirely new dimensions, reshaping industries such as gaming, education, and healthcare. In medicine, AI-powered diagnostic tools assist doctors in detecting diseases earlier and more accurately, improving patient outcomes and reducing the burden on healthcare systems. Autonomous vehicles, once a futuristic concept, are becoming a reality, promising to revolutionize transportation and reduce traffic fatalities.

Yet, with all these advancements, there remains an underlying question: What does it mean to be human in an increasingly digital world? As machines become more capable, creative, and intelligent, society must grapple with ethical dilemmas regarding automation, job displacement, and the role of AI in decision-making. The balance between technological progress and human values must be carefully maintained to ensure that innovation benefits all of humanity rather than a select few.

Looking ahead, the future of technology holds both promise and uncertainty. The continued development of quantum computing could unlock new frontiers in problem-solving, while breakthroughs in biotechnology might extend human lifespans and eradicate diseases. Space exploration, once the domain of government agencies, is now being pursued by private companies, raising the possibility of colonization beyond Earth. The next decades will be defined by our ability to navigate these rapid changes, making choices that prioritize sustainability, equity, and the well-being of future generations.

As individuals, organizations, and societies, we must remain vigilant, thoughtful, and forward-thinking, ensuring that the digital revolution remains a force for good in an ever-changing world.
"""
fp1 = get_fingerprint(text1)
fp2 = get_fingerprint(text2)

distance = sum(1 for b1, b2 in zip(fp1, fp2) if b1 != b2)

print(distance)