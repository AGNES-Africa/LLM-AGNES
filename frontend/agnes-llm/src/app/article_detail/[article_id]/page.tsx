"use client"
import ArticleDetailView from "../../components/ArticleDetailView";

export default function Article({params}:any) {
  return(
    <div className="mt-4">
      <ArticleDetailView
        article_id={params.article_id}
      />
    </div>
  )
}
