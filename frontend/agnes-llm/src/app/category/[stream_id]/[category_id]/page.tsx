"use client"
import ArticleListTable from "../../../components/ArticleListTable";

export default function ArticleList({params}:any) {
  return(
    <section className="py-24">
      <div className="container">
        <h1 className="text-3xl font-bold">Article List</h1>
        <ArticleListTable
          stream_id={params.stream_id}
          category_id={params.category_id}
        />
      </div>
    </section>
  )
}
