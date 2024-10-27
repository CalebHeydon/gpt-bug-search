#!/usr/bin/env python3

import sys
import os
from openai import OpenAI

if __name__ != "__main__":
    exit(-1)

if len(sys.argv) < 2:
    print(f"usage: {sys.argv[0] if len(sys.argv) > 0 else './search.py'}")
    exit(-1)

functions = []

for file in sys.argv[1:]:
    lines = []
    with open(file) as fd:
        for line in fd:
            lines.append(line)

            if line.startswith("}"):
                for i in reversed(range(len(lines) - 1)):
                    j = 0
                    if lines[i].startswith("{"):
                        j = i
                    elif not lines[i].startswith(" ") and not lines[i].startswith("\t") and lines[i].strip().endswith("{"):
                        j = i + 1
                    else:
                        continue

                    signature = lines[j - 1].strip()
                    if signature.endswith("{"):
                        signature = signature[:-1].strip()

                    if j > 1 and len(lines[j - 1].strip()) > 0 and "}" not in lines[j - 1] and "#" not in lines[j - 1]:
                        j -= 1
                        signature = lines[j - 1].strip() + " " + signature

                    if len(signature.split()) < 3 and signature.startswith("struct") or len(signature.split()) > 2 and signature.split()[0] == "typedef" and signature.split()[1] == "struct":
                        continue

                    function = ""
                    for k in range(j - 1, len(lines)):
                        function += lines[k]
                    functions.append((f"{file}:{j}", signature, function))
                    break

chats = []
input_tokens = 0
for function in functions:
    location = function[0]
    signature = function[1]
    code = function[2]

    chats.append((location, signature, f"Are there any security-related bugs in the following C function? Please respond in the form of a likelyhood 1-10/10 followed by a newline and a one-sentence explanation.\n\n{code}"))
    input_tokens += len(chats[-1][2].split())

output_tokens = len(chats) * 100 # ~100 token response
cost = input_tokens / 1e6 * 2.5 + output_tokens / 1e6 * 10
user_response = input(f"The estimated cost is ${cost}. Would you like to proceed? [y/N] ")
if user_response.strip() != "y":
    exit()

key = os.environ.get("OPENAI_API_KEY")
if not key:
    print("Please specify an OpenAI api key using the OPENAI_API_KEY environment variable")
    exit(-1)
client = OpenAI(api_key=key)

print()
for chat in chats:
    response = client.chat.completions.create(messages=[{"role":"user", "content":chat[2]}], model="gpt-4o").choices[0].message.content
    severity = response.split("\n")[0].strip()
    explanation = response[response.find("\n") + 1:].strip()

    print(f"{chat[0]}\t{chat[1]}\n{severity}\n{explanation}\n")
