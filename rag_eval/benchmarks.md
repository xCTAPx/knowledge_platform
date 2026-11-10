Vectors only
Hit@5  1.000  (40/40)
MRR@5  0.790
Recall@5  0.950
NDCG@5  0.788
Precision@5  0.240
Latency  mean 4257 ms   p50 4284 ms   p95 4346 ms

BM-25
Hit@5  0.950  (38/40)
MRR@5  0.844
Recall@5  0.912
NDCG@5  0.839
Precision@5  0.235
Latency  mean 4137 ms   p50 4139 ms   p95 4166 ms

Vectors + Reranking
Hit@5  1.000  (40/40)
MRR@5  0.912
Recall@5  1.000
NDCG@5  0.927
Precision@5  0.260
Latency  mean 4799 ms   p50 4797 ms   p95 4841 ms

Vectors + BM-25 + Reranking
Hit@5  1.000  (40/40)
MRR@5  0.912
Recall@5  1.000
NDCG@5  0.927
Precision@5  0.260
Latency  mean 9105 ms   p50 9138 ms   p95 9238 ms

ragas (Vectors + BM-25 + Reranking)
faithfulness  0.935
answer_relevancy  0.827
llm_context_precision_with_reference  0.860
context_recall  0.988
factual_correctness(mode=f1)  0.532

