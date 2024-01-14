from openai import OpenAI
import json

def generateName(client, blog_topic):
	return json.loads(
		client.chat.completions.create(
			model='gpt-3.5-turbo-1106',
			response_format={'type': 'json_object'},
			messages=[
				{'role': 'system', 'content': "You generate blog names based on what the blog is about. Be creative and not too cheesy or cliché. The name should be modern, sophisticated, and sleek. You must respond in JSON format as follows: \{'name': 'BLOG NAME HERE'\}"},
				{'role': 'user', 'content': f"Generate me a name for a blog about {blog_topic}"},
			]
		).choices[0].message.content)['name']

def generatePostTopics(client, blog_name, blog_topic, number_of_posts):
	return json.loads(
		client.chat.completions.create(
			model='gpt-3.5-turbo-1106',
			response_format={'type': 'json_object'},
			messages=[
				{'role': 'system', 'content': "You generate blog posts based on what the blog is called and about. Be creative and not too cheesy or cliché. The name should be modern, sophisticated, and sleek. You must respond in JSON format as follows: \{'posts':[POST OBJECTS]\} where each POST OBJECT consists of a 'title' and 'summary'."},
				{'role': 'user', 'content': f"Generate me {number_of_posts} unqiue posts for a blog named {blog_name} about {blog_topic}"},
			]
		).choices[0].message.content)['posts']

def generatePostSections(client, blog_name, blog_topic, post_title, post_summary):
	return json.loads(
		client.chat.completions.create(
			model='gpt-3.5-turbo-1106',
			response_format={'type': 'json_object'},
			messages=[
				{'role': 'system', 'content': "You generate sections of a blog post based on what the blog is called and about, what the post is titled, and a brief summary of the post. Be creative and not too cheesy or cliché. The tone should be modern, sophisticated, and sleek. Aside from the body sections, there must be a section with the title 'Introduction' and a section with the title 'Conclusion'. You must respond in JSON format as follows: \{'sections':[SECTION OBJECTS]\} where each SECTION OBJECT consists of a 'title' and 'summary'."},
				{'role': 'user', 'content': f"Generate me sections for a post for a blog named {blog_name} about {blog_topic}. The post is titled {post_title} and a brief summary is '{post_summary}'."},
			]
		).choices[0].message.content)['sections']

def generateSectionContent(client, blog_name, blog_topic, post_title, post_summary, section_title, section_summary):
	return json.loads(
		client.chat.completions.create(
			model='gpt-3.5-turbo-1106',
			response_format={'type': 'json_object'},
			messages=[
				{'role': 'system', 'content': "You generate the content for a section of a blog post based on what the blog is called and about, what the post is titled, a brief summary of the post, the section title, and a brief summary of the section. Be creative and not too cheesy or cliché. The tone should be modern, sophisticated, and sleek. You should generate 4 to 6 paragraphs of content. Each paragraph is separated by 2 line breaks. You must respond in JSON format as follows: \{'paragraphs':[PARAGRAPH STRINGS]\} where each PARAGRAPH STRING is 3 to 4 sentences long."},
				{'role': 'user', 'content': f"Generate me content for a section in a post for a blog named {blog_name} about {blog_topic}. The post is titled {post_title} and a brief summary of the post is '{post_summary}'. The section is titled {section_title} and a brief summary of the section is {section_summary}"},
			]
		).choices[0].message.content)['paragraphs']

if __name__ == '__main__':
	from config import *

	client = OpenAI(api_key=OPENAI_API_KEY)

	topic = 'personal finance'

	name = generateName(client, topic)
	print(name)

	posts = generatePostTopics(client, name, topic, 1)

	for post in posts:
		print(f"# {post['title']}")
		sections = generatePostSections(client, name, topic, post['title'], post['summary'])
		for section in sections:
			print(f"## {section['title']}")
			section_content = generateSectionContent(client, name, topic, post['title'], post['summary'], section['title'], section['summary'])
			print(section_content)
		print()