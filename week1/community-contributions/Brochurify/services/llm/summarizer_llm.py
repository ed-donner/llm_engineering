from abc import abstractmethod, ABC


class BaseSummarizer(ABC):

    @abstractmethod
    async def generate(self, *args, **kwargs):
        pass

    @abstractmethod
    async def remove_unnecessary_link(self, *args, **kwargs):
        pass

    def prompts_for_removing_links(self, url, links, description=None, site_type=None):
        link_system_prompt = (
            "You are provided with a list of links found on a webpage. "
            "Your task is to filter out irrelevant links and retain those that are most\
             relevant for creating a brochure. "
            "Consider links that provide valuable information about the site's content,\
             such as main articles, key information pages, or other significant sections.\n"
            "Exclude links that are not useful for a brochure, such as Terms of Service,\
             Privacy policies, and email links.\n"
            "You should respond in JSON format as shown in the example below:\n"
            "{\n"
            '    "links": [\n'
            '        {"type": "relevant page type", "url": "https://full.url/goes/here"},\n'
            '        {"type": "another relevant page type", "url": "https://another.full.url"}\n'
            "    ]\n"
            "}"
        )

        user_prompt = self.get_links_user_prompt(url, links, description, site_type)

        return [
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    def get_links_user_prompt(url, links, description=None, site_type=None):
        user_prompt = f"Here is the list of links found on the {url}:\n"

        if site_type or description:
            user_prompt += "Additional context:\n"
            if site_type:
                user_prompt += f"- Site type: {site_type}\n"
            if description:
                user_prompt += f"- User description: {description}\n"

        user_prompt += (
            "Please evaluate the following links and select those that are relevant for inclusion in a brochure. "
            "Exclude links related to Terms of Service, Privacy policies, and email addresses.\n"
            "Links (some might be relative links):\n"
        )
        user_prompt += "\n".join(links)
        return user_prompt
