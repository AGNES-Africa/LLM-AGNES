"use client"
import ArticleView from "@/components/ArticleView";

export default function Article({params}:any) {
  return(
    <div className="mt-4">
      <ArticleView
        article_id={params.article_id}
      />
    </div>
  )
}
