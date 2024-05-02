"use client"
import ArticleListTable from "@/components/ArticleListAllTable";

export default function ArticleList({params}:any) {
  return(
    <div className="mt-1">
      <ArticleListTable
        stream_id={params.stream_id}
        category_id={params.category_id}
      />
    </div>
  )
}
