
def compute_end_index(len: int, skip: int = 0, limit: int = 0) -> (int, int):

    end = len
    if len > (skip + limit):
        end = skip + limit
    if limit == 0:
        end = len
    return skip, end
