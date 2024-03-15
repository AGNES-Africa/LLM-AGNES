"use client"
import ArticleView from "../../components/ArticleView";

export default function Article({params}:any) {
  return(
    <section className="py-24">
      <div className="container">
        <h1 className="text-3xl font-bold">Article List</h1>
        <ArticleView
          article_id={params.article_id}
        />
      </div>
    </section>
  )
}
