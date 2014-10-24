var main = function() {
    db.attachment.find().forEach(function(obj){
        db.attachment.update({_id: obj._id}, {$pull: {prize_ids: 1}})
    })
}
