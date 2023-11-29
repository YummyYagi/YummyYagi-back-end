import random
import time
import openai

def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 3,
):
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specified errors
            
            except openai.RateLimitError as e:
                print(e)
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())

                # Sleep for the delay
                time.sleep(delay)
            
            except openai.BadRequestError as e:
                
                print(e)
                cur_kwargs=kwargs
                cur_prompt=cur_kwargs['prompt']
                
                n_gram_range = (2, 2)
                stop_words = "english"
                count = CountVectorizer(ngram_range=n_gram_range, stop_words=stop_words).fit([cur_prompt])
                candidates = count.get_feature_names_out()

                model = SentenceTransformer('distilbert-base-nli-mean-tokens')
                doc_embedding = model.encode([cur_prompt])
                candidate_embeddings = model.encode(candidates)
                top_n = 1
                distances = cosine_similarity(doc_embedding, candidate_embeddings)
                keywords = [candidates[index] for index in distances.argsort()[0][-top_n:]]
                print(keywords)
                cur_kwargs['prompt']=f'"{keywords}" in a drawing style of fairy tale'
                
                return func(*args, **cur_kwargs)

            # Raise exceptions for any errors not specified
            except Exception as e:
                print(e)
                raise e

    return wrapper

