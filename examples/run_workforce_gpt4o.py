from camel.toolkits import (
    VideoAnalysisToolkit,
    SearchToolkit,
    CodeExecutionToolkit,
    ImageAnalysisToolkit,
    DocumentProcessingToolkit,
    AudioAnalysisToolkit,
    AsyncBrowserToolkit,
    ExcelToolkit,
    FunctionTool
)
from camel.models import ModelFactory
from camel.types import(
    ModelPlatformType,
    ModelType
)

from camel.tasks import Task
from dotenv import load_dotenv

load_dotenv(override=True)

import os
import json
from typing import List, Dict, Any
from loguru import logger

from utils import OwlWorkforceChatAgent, OwlWorkforce
from retry import retry

from utils.gaia import GAIABenchmark

import shutil


def construct_agent_list() -> List[Dict[str, Any]]:
    

    web_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O,
        model_config_dict={"temperature": 0},
    )
    
    document_processing_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O,
        model_config_dict={"temperature": 0},
    )   
    
      
    reasoning_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.O3_MINI,
        model_config_dict={"temperature": 0},
    )
    
    image_analysis_model = ModelFactory.create( 
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O,
        model_config_dict={"temperature": 0},
    )
    
    video_analysis_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O,
        model_config_dict={"temperature": 0},
    )
    
    audio_reasoning_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.O3_MINI,
        model_config_dict={"temperature": 0},
    )
    
    web_agent_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O,
        model_config_dict={"temperature": 0},
    )
    
    planning_agent_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.O3_MINI,
        model_config_dict={"temperature": 0},
    )
    

    search_toolkit = SearchToolkit()
    document_processing_toolkit = DocumentProcessingToolkit(cache_dir="tmp")
    image_analysis_toolkit = ImageAnalysisToolkit(model=image_analysis_model)
    video_analysis_toolkit = VideoAnalysisToolkit(download_directory="tmp/video")
    # audio_analysis_toolkit = AudioAnalysisToolkit(cache_dir="tmp/audio", audio_reasoning_model=audio_reasoning_model)
    audio_analysis_toolkit = AudioAnalysisToolkit(cache_dir="tmp/audio", reasoning=True)
    # video_analysis_toolkit = VideoAnalysisToolkit(download_directory="tmp/video", model=video_analysis_model, use_audio_transcription=True)
    code_runner_toolkit = CodeExecutionToolkit(sandbox="subprocess", verbose=True)
    browser_simulator_toolkit = AsyncBrowserToolkit(headless=True, cache_dir="tmp/browser", planning_agent_model=planning_agent_model, web_agent_model=web_agent_model)
    excel_toolkit = ExcelToolkit()
    
#     search_agent = OwlWorkforceChatAgent(
#         """
# Please act as a search agent, constructing appropriate keywords and searach terms, using search toolkit to collect relevant information, including urls, webpage snapshots, etc.
# Here are some tips that help you perform web search:
# - Never add too many keywords in your search query! Some detailed results need to perform browser interaction to get, not using search toolkit.
# - If the question is complex, search results typically do not provide precise answers. It is not likely to find the answer directly using search toolkit only, the search query should be concise and focuses on finding official sources rather than direct answers.
#   For example, as for the question "What is the maximum length in meters of #9 in the first National Geographic short on YouTube that was ever released according to the Monterey Bay Aquarium website?", your first search term must be coarse-grained like "National Geographic YouTube" to find the youtube website first, and then try other fine-grained search terms step-by-step to find more urls.
# You can provide multiple url results and relevant information.
#         """,
#         web_model,
#         tools=[
#             FunctionTool(search_toolkit.search_google),
#             #FunctionTool(search_toolkit.search_archived_webpage),
#         ]
#     )
# """
# Here are some tips that help you perform web search:
# - Never add too many keywords in your search query! Some detailed results need to perform browser interaction to get, not using search toolkit.
# - If the question is complex, search results typically do not provide precise answers. It is not likely to find the answer directly using search toolkit only, the search query should be concise and focuses on finding official sources rather than direct answers.
#   For example, as for the question "What is the maximum length in meters of #9 in the first National Geographic short on YouTube that was ever released according to the Monterey Bay Aquarium website?", your first search term must be coarse-grained like "National Geographic YouTube" to find the youtube website first, and then try other fine-grained search terms step-by-step to find more urls.
# """

    web_agent = OwlWorkforceChatAgent(
"""
You are a helpful assistant that can search the web, extract webpage content, simulate browser actions, and provide relevant information to solve the given task.
Keep in mind that:
- Do not be overly confident in your own knowledge. Searching can provide a broader perspective and help validate existing knowledge.  
- If one way fails to provide an answer, try other ways or methods. The answer does exists.
- If the search snippet is unhelpful but the URL comes from an authoritative source, try visit the website for more details.  
- When looking for specific numerical values (e.g., dollar amounts), prioritize reliable sources and avoid relying only on search snippets.  
- When solving tasks that require web searches, check Wikipedia first before exploring other websites.  
- You can also simulate browser actions to get more information or verify the information you have found.
- Browser simulation is also helpful for finding target URLs. Browser simulation operations do not necessarily need to find specific answers, but can also help find web page URLs that contain answers (usually difficult to find through simple web searches). You can find the answer to the question by performing subsequent operations on the URL, such as extracting the content of the webpage.
- Do not solely rely on document tools or browser simulation to find the answer, you should combine document tools and browser simulation to comprehensively process web page information. Some content may need to do browser simulation to get, or some content is rendered by javascript.
- In your response, you should mention the urls you have visited and processed.

Here are some tips that help you perform web search:
- Never add too many keywords in your search query! Some detailed results need to perform browser interaction to get, not using search toolkit.
- If the question is complex, search results typically do not provide precise answers. It is not likely to find the answer directly using search toolkit only, the search query should be concise and focuses on finding official sources rather than direct answers.
  For example, as for the question "What is the maximum length in meters of #9 in the first National Geographic short on YouTube that was ever released according to the Monterey Bay Aquarium website?", your first search term must be coarse-grained like "National Geographic YouTube" to find the youtube website first, and then try other fine-grained search terms step-by-step to find more urls.
- The results you return do not have to directly answer the original question, you only need to collect relevant information.
""",
        model=web_model,
        tools=[
            # FunctionTool(search_toolkit.search_google),
            # FunctionTool(search_toolkit.search_wiki),
            # FunctionTool(search_toolkit.search_wiki_revisions),
            FunctionTool(search_toolkit.web_search),
            FunctionTool(document_processing_toolkit.extract_document_content),
            FunctionTool(browser_simulator_toolkit.browse_url) ,
            FunctionTool(video_analysis_toolkit.ask_question_about_video),
            #FunctionTool(search_toolkit.search_archived_webpage),
        ]
    )
    
    document_processing_agent = OwlWorkforceChatAgent(
        "You are a helpful assistant that can process documents and multimodal data, such as images, audio, and video.",
        document_processing_model,
        tools=[
            FunctionTool(document_processing_toolkit.extract_document_content),
            FunctionTool(image_analysis_toolkit.ask_question_about_image),
            FunctionTool(audio_analysis_toolkit.ask_question_about_audio),
            FunctionTool(video_analysis_toolkit.ask_question_about_video),
            FunctionTool(code_runner_toolkit.execute_code),
        ]
    )
    
    reasoning_coding_agent = OwlWorkforceChatAgent(
        "You are a helpful assistant that specializes in reasoning and coding, and can think step by step to solve the task. When necessary, you can write python code to solve the task. If you have written code, do not forget to execute the code. Never generate codes like 'example code', your code should be able to fully solve the task. You can also leverage multiple libraries, such as requests, BeautifulSoup, re, pandas, etc, to solve the task. For processing excel files, you should write codes to process them.",
        reasoning_model,
        tools=[
            FunctionTool(code_runner_toolkit.execute_code),
            FunctionTool(excel_toolkit.extract_excel_content),
            FunctionTool(document_processing_toolkit.extract_document_content),
        ]
    )

    agent_list = []
    
    # search_agent_dict = {
    #     "name": "Search Agent",
    #     "description": "A helpful assistant that can construct appropriate search queries based on the user's request and perform web searches.",
    #     "agent": search_agent
    # }
    
    web_agent_dict = {
        "name": "Web Agent",
        "description": "A helpful assistant that can search the web, extract webpage content, simulate browser actions, and retrieve relevant information.",
        "agent": web_agent
    }
    
    document_processing_agent_dict = {
        "name": "Document Processing Agent",
        "description": "A helpful assistant that can process a variety of local and remote documents, including pdf, docx, images, audio, and video, etc.",
        "agent": document_processing_agent
    }
    
    reasoning_coding_agent_dict = {
        "name": "Reasoning Coding Agent",
        "description": "A helpful assistant that specializes in reasoning, coding, and processing excel files. However, it cannot access the internet to search for information. If the task requires python execution, it should be informed to execute the code after writing it.",
        "agent": reasoning_coding_agent
    }

    
    # agent_list.append(search_agent_dict)
    agent_list.append(web_agent_dict)
    agent_list.append(document_processing_agent_dict)
    # agent_list.append(multimodal_processor_agent_dict)
    agent_list.append(reasoning_coding_agent_dict)
    return agent_list


def construct_workforce() -> OwlWorkforce:
      
    task_agent_kwargs = {
        "model": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        )
    }
    
    coordinator_agent_kwargs = {
        "model": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.O3_MINI,
            model_config_dict={"temperature": 0},
        )
    }
    
    workforce = OwlWorkforce(
        "Gaia Workforce",
        task_agent_kwargs=task_agent_kwargs,
        coordinator_agent_kwargs=coordinator_agent_kwargs,
    )

    agent_list = construct_agent_list()
    
    for agent_dict in agent_list:
        workforce.add_single_agent_worker(
            agent_dict["description"],
            worker=agent_dict["agent"],
            name=agent_dict["name"],
        )

    return workforce


def evaluate_on_gaia():
    
    # level 1: [2, 7, 12, 14, 15, 24, 27, 29, 40, 42, 43, 45, 46, 52]
    # level 2: [0, 2, 6, 15, 16, 19, 27, 32, 33, 36, 37, 40, 42, 45, 57, 66, 68, 69, 79]
    # level 3: [5, 10, 11, 13, 21, 25]
    
    LEVEL = 2
    on="valid"
    SAVE_RESULT = True
    MAX_TRIES = 1
    # SAVE_RESULT_PATH = f"results/workforce/workforce_{LEVEL}_pass{MAX_TRIES}.json"
    SAVE_RESULT_PATH = f"results/test/workforce_{LEVEL}_pass{MAX_TRIES}.json"

    test_idx = []

    # tune prompt: 79

    if os.path.exists(f"tmp/"):
        # delete all files in 
        # the tmp folder
        shutil.rmtree(f"tmp/")
    
    benchmark = GAIABenchmark(
        data_dir="data/gaia",
        save_to=SAVE_RESULT_PATH,
    )
    
    # Concurrently run 3 workers
    result = benchmark.run_workforce_concurrently(
        construct_workforce,
        on=on,
        level=LEVEL,
        idx=test_idx,
        save_result=SAVE_RESULT,
        max_tries=MAX_TRIES,
        max_replanning_tries=3,
        max_workers=3
    )
    
    
    logger.success(f"Correct: {result['correct']}, Total: {result['total']}")
    logger.success(f"Accuracy: {result['accuracy']}")


if __name__ == "__main__":
    evaluate_on_gaia()

